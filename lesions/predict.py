import sys, torch, timm, cv2, numpy as np

classes = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
IMG = 224
MEL_FACTOR = 3.0

model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=7)
model.load_state_dict(torch.load("best.pth", map_location="cpu"))
model.eval()

mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def predict(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Image introuvable : {path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (IMG, IMG), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    img = (img - mean) / std
    x = torch.from_numpy(img.transpose(2, 0, 1)).unsqueeze(0)
    with torch.no_grad():
        p = torch.softmax(model(x), 1)[0].numpy()
    p[classes.index("mel")] *= MEL_FACTOR
    return p / p.sum()

if __name__ == "__main__":
    path = sys.argv[1]
    p = predict(path)
    print("Image :", path)
    for i in np.argsort(-p):
        print(f"{classes[i]:6s} {p[i]*100:5.1f} %")