# Use yolov8/v5 to detect cars, pedestrians, traffic signs, sidewalks
# Output bounding bxoes, class labels, confidence scores
# Use MDP with DQN to optimize rule-based policy
# Run through NVIDIA CNN model for final output
# Fuse together stuff

import torch

model = torch.hub.load("ultralytics/yolov5", "yolov5s") # yolov5n / yolov5x6 / custom

img = "https://ultralytics.com/images/zidane.jpg"
result = model(img)

result.print()