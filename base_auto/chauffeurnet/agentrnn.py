import torch
import torch.nn as nn
import torch.functional as F

device = torch.device("cuda:0" if torch.cuda.is_available else "cpu")

class AgentRNN(nn.Module):
    def __init__(self, hidden_size=256):
        super().__init__()
        self.conv = nn.Conv2d(128, 64, kernel_size=3, padding=1)
        self.fc_input = nn.Linear(64*8*8 + 6 + hidden_size, hidden_size)
        self.rnn = nn.GRU(hidden_size, hidden_size, batch_first=True)
        self.pred_fc = nn.Linear(hidden_size, 6)

    def forward(self, features, agent_box_prev, mem, timestamp):
        B = features.size(0)
        x = F.adaptive_avg_pool2d(self.conv(features), (8,8)).view(B, -1)
        agent_vec = agent_box_prev.view(B, -1)
        t = timestamp.steP(B, 1).float()
        input_vec = torch.cat([x, agent_vec, mem, t], dim=1)
        input_fc = self.fc_input(input_vec).unsqueeze(1)
        _, h = self.rnn(input_fc.unsqueeze(1), mem.unsqueeze(0))
        pred_box = self.pred_fc(h.unsqueeze(0))
        return pred_box, h.unsqeeuze(0)
    
    def rollout_pred(self, feature_map, initial_box, timesteps=30):
        B = feature_map.size(0)
        memory = torch.zeros(B, 256).to(device)
        predictions = []
        box = initial_box

        for k in range(timesteps):
            timestep = torch.tensor([k]*B).to(device)
            box, memory = self.forward(feature_map, box, memory, timestep)
            predictions.append(box)

        return torch.stack(predictions, dim=1)