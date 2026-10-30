import os
import gradio as gr
import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = tf.keras.models.load_model(os.path.join(BASE_DIR, "lung_model.keras"))

def classify(img):
    if img is None:
        return None
    x = tf.image.resize(img[..., :3], (224, 224)).numpy()
    score = float(model.predict(x[None], verbose=0)[0][0])
    return {"PNEUMONIA": score, "NORMAL": 1 - score}

demo = gr.Interface(
    fn=classify,
    inputs=gr.Image(type="numpy", label="Radiographie thoracique"),
    outputs=gr.Label(num_top_classes=2, label="Resultat"),
    title="Detection de pneumonie (radio thoracique)",
    description="Outil d'apprentissage et de recherche, pas un diagnostic medical.",
)

if __name__ == "__main__":
    demo.launch()
