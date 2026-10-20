import os
import pandas as pd

data_dir = "./autonomous/udacity-self-driving-car-behavioural-cloning/versions/1/self_driving_car_dataset_make"
log_path = os.path.join(data_dir, "driving_log.csv")

df = pd.read_csv(log_path)

# New base image path
base_path = os.path.abspath(os.path.join(data_dir, "IMG"))

# Update paths in DataFrame
for idx, row in df.iterrows():
    df.at[idx, "center"] = f"{base_path}/{os.path.basename(row['center'].strip())}"
    df.at[idx, "left"]   = f"{base_path}/{os.path.basename(row['left'].strip())}"
    df.at[idx, "right"]  = f"{base_path}/{os.path.basename(row['right'].strip())}"

# Save updated DataFrame
df.to_csv(log_path, index=False)
