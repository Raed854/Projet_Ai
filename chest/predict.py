import os, sys
import numpy as np
import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = tf.keras.models.load_model(os.path.join(BASE_DIR, "lung_model.keras"))
CLASSES = {0: "NORMAL", 1: "PNEUMONIA"}

def predict(path):
    img = tf.keras.utils.load_img(path, target_size=(224, 224))
    x = np.expand_dims(tf.keras.utils.img_to_array(img), 0)
    score = float(model.predict(x, verbose=0)[0][0])
    return CLASSES[int(score > 0.5)], score

target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "images_test")
if os.path.isdir(target):
    files = sorted(f for f in os.listdir(target) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    if not files:
        print("Aucune image trouvee dans", target)
    for f in files:
        label, score = predict(os.path.join(target, f))
        print(f"{f:45s} -> {label:10s} (score = {score:.3f})")
else:
    label, score = predict(target)
    print(f"{target} -> {label} (score = {score:.3f})")
