import torch
from PIL import Image
from torchvision import transforms
import numpy as np
from u2net import U2NET  # 請確保你有 u2net.py
import os

# 載入模型
def load_model():
    net = U2NET(3, 1)
    net.load_state_dict(torch.load('./u2net/u2net.pth', map_location='cpu'))
    net.eval()
    return net

model = load_model()

# 去背函式
def remove_background(input_path, output_path):
    image = Image.open(input_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((320, 320)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        d1, *_ = model(tensor)
        mask = d1[0][0].cpu().numpy()
        mask = (mask - mask.min()) / (mask.max() - mask.min())
        mask = Image.fromarray((mask * 255).astype(np.uint8)).resize(image.size)
        image.putalpha(mask)
        image.save(output_path)
