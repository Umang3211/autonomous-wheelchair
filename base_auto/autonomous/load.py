import os
import cv2
import pandas as pd
import numpy as np

data_dir = "./autonomous/udacity-self-driving-car-behavioural-cloning/versions/1/self_driving_car_dataset_make"
log_path = os.path.join(data_dir, "driving_log.csv")
img_dir = os.path.join(data_dir, "IMG")

df = pd.read_csv(log_path)

images = []
steering = []
throttle = []
brake = []
speed = []

target_width = 320
target_height = 160

for _, row in df.iterrows():
    img_path = os.path.join(img_dir, os.path.basename(row['center'].strip()))
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    img = cv2.resize(img, (target_width, target_height))

    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))

    images.append(img)
    steering.append(float(row['steering']))
    throttle.append(float(row['throttle']))
    brake.append(float(row['break']))
    speed.append(float(row['speed']))

    # print(f"Steering: {steering}, Throttle: {throttle}, Brake: {brake}")

X = np.array(images)
y = np.array(list(zip(steering, throttle, brake, speed)))