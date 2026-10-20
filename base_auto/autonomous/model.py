import torch
import torch.nn as nn
import torch.nn.functional as F
from load import X, y
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt

# for now, taking in center image only, later on can take from left + right viewpoints for optimization
import torch
import torch.nn as nn
import torch.nn.functional as F

X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)
dataset = TensorDataset(X_tensor, y_tensor)
dataloader = DataLoader(dataset, batch_size=64, shuffle=True)

class DrivingCNN(nn.Module):
    def __init__(self):
        super(DrivingCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 24, kernel_size=5, stride=2)
        self.conv2 = nn.Conv2d(24, 36, kernel_size=5, stride=2)
        self.conv3 = nn.Conv2d(36, 48, kernel_size=5, stride=2)
        self.conv4 = nn.Conv2d(48, 64, kernel_size=3, stride=1)
        self.conv5 = nn.Conv2d(64, 64, kernel_size=3, stride=1)

        # Compute flattened size manually: input is [3, 160, 320]
        self.fc_input_dim = self._get_flattened_size()

        self.fc1 = nn.Linear(self.fc_input_dim, 100)
        self.fc2 = nn.Linear(100, 50)
        self.fc3 = nn.Linear(50, 10)
        self.output = nn.Linear(10, 4)  # steering, throttle, brake, speed

    def _get_flattened_size(self):
        with torch.no_grad():
            x = torch.zeros(1, 3, 160, 320)
            x = self.conv1(x)
            x = self.conv2(x)
            x = self.conv3(x)
            x = self.conv4(x)
            x = self.conv5(x)
            return x.view(1, -1).shape[1]

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = F.relu(self.conv4(x))
        x = F.relu(self.conv5(x))
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        return self.output(x)

model = DrivingCNN()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

epochs = 45
loss_values = []
for epoch in range(epochs):
    model.train()
    for batch_X, batch_y in dataloader:
        preds = model(batch_X)
        loss = criterion(preds, batch_y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    loss_values.append(loss.item())
    print(f"Epoch: {epoch+1}, Loss: {loss.item():.4f}")

plt.plot(range(1, epochs+1), loss_values, marker='o', linestyle='-')
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training Loss Over Epochs")
plt.grid(True)
plt.show()

torch.save(model.state_dict(), "cnnautonomous.pt")