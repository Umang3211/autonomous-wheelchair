from cv2 import transform
import torch
import torchvision.transforms as transforms
from PIL import Image
from autonomous.model import DrivingCNN
from picamera2 import Picamera2

model = DrivingCNN()
model.load_state_dict("cnnautonomous.pt", map_location=torch.device("cuda" if torch.cuda.is_available else "cpu"))
model.eval()

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (320, 160)}))

while True:
    frame = picam2.capture_array()
    img = Image.fromarray(frame)
    input_tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        output = model(input_tensor)

    tensor_output = output # [steering, throttle, break, speed]

# make chair move
