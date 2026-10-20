import torch
import torch.nn as nn
import torch.nn.functional as F
# from carla import VehicleControl

class BEVRenderer:
    def __init__(self, size=256, pixels_per_meter=2):
        self.size = size
        self.pixels_per_meter = pixels_per_meter

    def render(self, agents, road_mask, ego_state):
        bev = torch.zeros(8, self.size, self.size)
        bev[0] = torch.from_numpy(road_mask).float()

        for agent in agents:
            x, y = self._world_to_pixel(agent.transform.location)
            bev[1:4, x-2:x+2, y-2:y+2] = 1.0

        ego_x, ego_y = self._world_to_pixel(ego_state.location)
        bev[4:7, ego_x-2:ego_x+2, ego_y-2:ego_y+2] = 1.0

        return bev
    
    def _world_to_pixel(self, location):
        x = int(location.x * self.pixels_per_meter + self.size//2)
        y = int(location.y * self.pixels_per_meter + self.size//2)
        return max(0, min(self.size-1, x)), max(0, min(self.size-1, y))
    
class FeatureNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(8, 64, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(3, stride=2),
            ResBlock(64, 64),
            ResBlock(64, 128, stride=2),
            ResBlock(128, 256, stride=2),
            nn.ReLU()
        )
    
class ResBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride, 1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))

        out += self.shortcut(x)
        return F.relu(out)

class AgentRNN(nn.Module):
    def __init__(self, input_size=256, hidden_size=512):
        super().__init__()
        self.lstm = nn.LSTMCell(input_size + 256, hidden_size)
        self.waypoint_fc = nn.Linear(hidden_size, 3)
        self.heatmap_conv = nn.Conv2d(1, 1, 3, padding=1)

    def forward(self, features, memory, hidden_state):
        hx, cx = self.lstm(torch.cat([features, memory.flatten(1)], 1), hidden_state)
        waypoint = self.waypoint_fc(hx)

        heatmap = self.heatmap_conv(memory)
        new_mem = memory + F.sigmoid(heatmap)

        return waypoint, (hx, cx), new_mem
    
# sestup road mask prediction net + perceptionRNN
class PerceptionRNN(nn.Module):
    def __init__(self,  agent_num, input_size=256, hidden_size=512):
        super().__init__()
        self.agent_num = agent_num
        self.lstm = nn.LSTMCell(input_size + 256, hidden_size)
        self.heatmap_conv = nn.Conv2d(hidden_size, agent_num, 1, padding=1) # change dims prob

    def forward(self, features, memory, hidden_state, steps=10):
        batch_size = features.size(0)
        hx = torch.zeros(batch_size, 512, device=features.device)
        cx = torch.zeros_like(hx)
        agent_heatmaps = []
        for _ in range(steps):
            hx, cx = self.lsm(torch.cat([features, memory.flatten(1)], 1), (hx, cx))

            # Reshaping for convolution
            hx_reshaped = hx.view(batch_size, 512, 1, 1)
            heatmap = self.heatmap_conv(hx_reshaped)
            agent_heatmaps.append(heatmap)

        agent_heatmaps = torch.stack(agent_heatmaps, dim=1) # [batch, steps, agent_num, 1, 1]
        return agent_heatmaps.squeeze(-1).unsqueeze(-1) # [batch, steps, agent_num]
    
class ChauffeurNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.feature_net = FeatureNet()
        self.agent_rnn = AgentRNN()
        self.perception_rnn = PerceptionRNN()

        self.road_head = nn.Sequential(
            nn.Conv2d(256, 128, 3, padding=1),
            nn.LeakyReLU(),
            nn.Conv2d(128, 1, 1)
        )

        self.perception_head = nn.Conv2d(256, 1, 3, padding=1)
        self.collision_head = nn.Conv2d(256, 1, 3, padding=1)

    def forward(self, benv_input, steps=10):
        features = self.feature_ent(benv_input)
        batch_size = features.size(0)

        memory = torch.zeros(batch_size, 1, 16, 16, device=benv_input.device)
        hx = torch.zeros(batch_size, 512, device=benv_input.device)
        cx = torch.zeros_like(hx)

        waypoints = []
        for _ in range(steps):
            wp, (hx, cx), memory = self.agent_rnn(
                F.adaptive_avg_pool2d(features, 1).flatten(1),
                memory,
                (hx, cx)
            )
        waypoints.append(wp)

        road_mask = self.road_head(features)
        agent_heatmap = self.perception_head(features)
        collision_heatmap = self.collision_head(features)

        # get other heatmap preds
        other_agent_heatmaps = self.perception_rnn(F.adaptive_avg_pool2d(features, 1).flatten(1), memory, (hx, cx), steps=steps)

        return (torch.stack(waypoints, 1), road_mask, agent_heatmap, collision_heatmap, other_agent_heatmaps)
    
class ChauffeurLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.weights = {'waypoint': 1.0, 'road': 0.5, 'heatmap': 0.5, 'collision': 1.0}

    @staticmethod
    def collision_loss(pred_agent_box, other_agent_heatmaps):
        combined_mask = other_agent_heatmaps.sum(2)
        return (pred_agent_box * combined_mask).mean()

    def forward(self, pred, target):
        waypoint_loss = F.mse_loss(pred['waypoints'], target['waypoints'])
        road_loss = F.binary_cross_entropy_with_logits(pred['road'], target['road_mask'])
        heatmap_loss = F.binary_cross_entropy_with_logits(pred['heatmap'], target['agent_heatmap'])
        collision_loss_val = self.collision_loss(pred['collision'], target['other_agent_heatmaps'])

        return (self.weights['waypoint'] * waypoint_loss + self.weights['road'] * road_loss + self.weights['heatmap'] * heatmap_loss + self.weights['collision'] * collision_loss_val)

if __name__ == "__main__":
    model = ChauffeurNet()
    loss_fn = ChauffeurLoss()

    dummy_input = torch.randn(4, 8, 256, 256)
    dummy_target = {
        'waypoints': torch.randn(4, 10, 3),
        'road_mask': torch.randn(4, 1, 256, 256),
        'agent_heatmap': torch.randn(4, 1, 256, 256),
        'agent_collision': torch.randn(4, 1, 256, 256)
    }

    optimizer = torch.optim.Adam(model.parameters())
    pred_waypoints, pred_road, pred_heatmap, pred_collision, other_agent_heatmaps = model(dummy_input)
    loss = loss_fn({
        'waypoints': pred_waypoints,
        'road': pred_road,
        'heatmap': pred_heatmap,
        'collision': pred_collision,
        'other_agent_heatmaps': other_agent_heatmaps
    }, dummy_target)

    loss.backward()
    optimizer.step()