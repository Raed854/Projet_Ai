import os, glob, torch, timm, cv2, numpy as np, gradio as gr

# ---------- CONFIG ----------
MODEL_NAME = "efficientnet_b0"
WEIGHTS = "best.pth"
IMG = 224
MEL_FACTOR = 3.0                 # à régler sur la validation
TTA = True                       # moyenne de 4 vues (image + flips)
LOW, HIGH = 0.10, 0.30           # seuils de la jauge de vigilance
# ----------------------------

classes = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
labels = {"akiec": "Kératose actinique (akiec)", "bcc": "Carcinome basocellulaire (bcc)",
          "bkl": "Kératose bénigne (bkl)", "df": "Dermatofibrome (df)",
          "mel": "Mélanome (mel)", "nv": "Naevus (nv)", "vasc": "Lésion vasculaire (vasc)"}
MEL = classes.index("mel")
SUSPECT = [classes.index(c) for c in ("mel", "bcc", "akiec")]

if not os.path.exists(WEIGHTS):
    raise SystemExit(
        f"Fichier '{WEIGHTS}' introuvable dans {os.getcwd()}.\n"
        "Mets le fichier dans ce dossier (à côté de app.py)."
    )

model = timm.create_model(MODEL_NAME, pretrained=False, num_classes=7)
model.load_state_dict(torch.load(WEIGHTS, map_location="cpu"))
model.eval()

print(f"Modèle chargé : {MODEL_NAME} | {IMG}px | TTA={TTA} | poids={WEIGHTS}")
INFO = (f"**Modèle :** {MODEL_NAME} · **Résolution :** {IMG}px · "
        f"**TTA :** {'oui (4 vues)' if TTA else 'non'} · **Poids :** {WEIGHTS}")

mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
std = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def to_rgb(img):
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    if img.shape[2] == 4:
        return img[:, :, :3]
    return img


def preprocess(img):
    img = cv2.resize(to_rgb(img), (IMG, IMG), interpolation=cv2.INTER_AREA)
    x = torch.from_numpy(((img.astype(np.float32) / 255.0 - mean) / std)
                         .transpose(2, 0, 1)).unsqueeze(0)
    return img, x


def predict_probs(x):
    views = [x, x.flip(3), x.flip(2), x.flip((2, 3))] if TTA else [x]
    with torch.no_grad():
        ps = [torch.softmax(model(v), 1)[0].numpy() for v in views]
    tops = []
    for q in ps:
        r = q.copy()
        r[MEL] *= MEL_FACTOR
        tops.append(int(r.argmax()))
    p = np.mean(ps, 0)
    p[MEL] *= MEL_FACTOR
    p = p / p.sum()
    agree = tops.count(int(p.argmax()))
    return p, agree, len(views)


def gradcam(x, idx):
    acts = {}
    h = model.conv_head.register_forward_hook(lambda m, i, o: acts.__setitem__("a", o))
    with torch.enable_grad():
        out = model(x)
        a = acts["a"]
        g = torch.autograd.grad(out[0, idx], a)[0]
    h.remove()
    w = g.mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((w * a).sum(1))[0].detach().numpy()
    cam = cv2.resize(cam, (IMG, IMG))
    return (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)


def gauge_html(score):
    pct = int(round(score * 100))
    if score < LOW:
        color, level = "#2e9e5b", "Vigilance faible"
    elif score < HIGH:
        color, level = "#e8a317", "Vigilance modérée"
    else:
        color, level = "#d64545", "Vigilance élevée"
    return f"""
    <div style="padding:8px 0">
      <div style="display:flex;justify-content:space-between;font-weight:600;font-size:16px">
        <span>{level}</span><span>{pct} %</span>
      </div>
      <div style="background:#d1d5db;border-radius:999px;height:24px;overflow:hidden;margin-top:6px">
        <div style="width:{pct}%;height:100%;background:{color}"></div>
      </div>
      <div style="font-size:12px;opacity:.7;margin-top:6px">
        Somme des probabilités de mélanome, carcinome basocellulaire et kératose actinique.
      </div>
    </div>"""


def analyze(img):
    if img is None:
        return {}, None, "Importe une image pour lancer l'analyse.", ""
    img, x = preprocess(img)
    p, agree, n = predict_probs(x)
    top = int(p.argmax())

    cam = gradcam(x, top)
    heat = cv2.cvtColor(cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET),
                        cv2.COLOR_BGR2RGB)
    overlay = (0.6 * img + 0.4 * heat).astype(np.uint8)

    score = float(p[SUSPECT].sum())
    text = f"### Résultat : {labels[classes[top]]} ({p[top] * 100:.0f} %)\n\n"
    if score >= HIGH:
        text += ("⚠️ Le modèle détecte un type de lésion potentiellement malin ou "
                 "précancéreux. Seul un dermatologue peut confirmer.")
    elif score >= LOW:
        text += ("Le modèle hésite : une part non négligeable de la probabilité va vers "
                 "une lésion suspecte. Un avis médical est conseillé en cas de doute.")
    else:
        text += ("Le modèle ne détecte pas de signe de malignité, mais cela ne "
                 "garantit rien.")
    text += f"\n\n🔁 **Cohérence :** {agree}/{n} vues donnent le même résultat."

    scores = {labels[c]: float(p[i]) for i, c in enumerate(classes)}
    return scores, overlay, text, gauge_html(score)


with gr.Blocks(title="Détection de lésions cutanées") as demo:
    gr.Markdown("# 🔬 Détection de lésions cutanées\n"
                "Projet d'apprentissage entraîné sur HAM10000 (images dermoscopiques). "
                "**Ne remplace pas un diagnostic médical.**")
    gr.Markdown(INFO)

    with gr.Accordion("📊 Performances du modèle (jeu de validation)", open=False):
        gr.Markdown("""
| Métrique | Résultat |
|---|---|
| Accuracy | 0.83 |
| F1 moyen (7 classes) | 0.71 |
| Recall mélanome | 0.64 (0.77 avec le facteur ×3) |
| Précision mélanome | 0.56 (0.49 avec le facteur ×3) |

_Mesuré sur 2 024 images, séparées par lésion. Le même jeu a servi à choisir le meilleur
epoch : les chiffres sont donc un peu optimistes._
""")

    with gr.Row():
        with gr.Column():
            inp = gr.Image(type="numpy", label="Image de la lésion")
            btn = gr.Button("Analyser", variant="primary")
        with gr.Column():
            msg = gr.Markdown()
            gauge = gr.HTML()
            out = gr.Label(num_top_classes=4, label="Probabilités")
            cam_img = gr.Image(label="Zone regardée par le modèle (Grad-CAM)")

    with gr.Accordion("📋 Règle ABCDE : à quoi faire attention", open=False):
        gr.Markdown("""
- **A**symétrie : les deux moitiés de la lésion ne se ressemblent pas
- **B**ords : irréguliers, dentelés ou mal délimités
- **C**ouleur : plusieurs teintes (brun, noir, rouge, blanc, bleu)
- **D**iamètre : supérieur à 6 mm
- **E**volution : la lésion change de taille, de forme ou de couleur

Une lésion nouvelle, qui saigne, qui gratte ou qui change mérite un avis
médical, quel que soit le résultat de ce modèle.
""")

    ex = sorted(glob.glob("examples/*.jpg"))
    if ex:
        gr.Examples(examples=[[p] for p in ex], inputs=inp, label="Exemples")

    btn.click(analyze, inputs=inp, outputs=[out, cam_img, msg, gauge])
    gr.Markdown("_Les pourcentages sont indicatifs : ils ne sont pas calibrés "
                "(le score du mélanome est volontairement amplifié)._")

demo.launch()