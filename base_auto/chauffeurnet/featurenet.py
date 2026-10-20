import torch
import torch.nn as nn

class FeatureNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels=9, out_channels=32, kernel_size=3, padding=1),
            nn.RelU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU()
        )

    def forward(self, x):
        return self.encoder(x) # [B, 128, H, W]