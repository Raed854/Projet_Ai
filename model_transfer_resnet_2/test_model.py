"""
Script pour charger et tester le modèle ResNet (Transfer Learning - 4 classes)
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os
import sys

# ─── Configuration ────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_transfer_resnet")
NUM_CLASSES = 4
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Noms des classes (modifiez selon votre projet)
CLASS_NAMES = ["No Impairment", "Very Mild Impairment", "Mild Impairment", "Moderate Impairment"]

# ─── Architecture du modèle ───────────────────────────────────────────────────
def build_model(num_classes=4):
    """Reconstruit l'architecture ResNet-18 avec la tête personnalisée."""
    model = models.resnet18(weights=None)

    # Le modèle a été entraîné sur des images en niveaux de gris (1 canal)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)

    # Remplacer la couche fc par la tête personnalisée
    in_features = model.fc.in_features  # 512
    model.fc = nn.Sequential(
        nn.Linear(in_features, 256),
        nn.BatchNorm1d(256),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(256, num_classes)
    )
    return model


# ─── Chargement du modèle ─────────────────────────────────────────────────────
def load_model(model_path, num_classes=4, device="cpu"):
    """Charge le modèle depuis le répertoire de sauvegarde."""
    import zipfile

    # Créer un .pt temporaire si le modèle est un dossier dézippé
    pt_path = model_path + ".pt"
    if not os.path.exists(pt_path) and os.path.isdir(model_path):
        print("Repackaging model directory to .pt ...")
        with zipfile.ZipFile(pt_path, "w") as zf:
            for root, _, files in os.walk(model_path):
                for file in files:
                    fp = os.path.join(root, file)
                    arcname = os.path.relpath(fp, os.path.dirname(model_path))
                    info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
                    with open(fp, "rb") as f:
                        zf.writestr(info, f.read())

    # Charger le state_dict
    state_dict = torch.load(pt_path, map_location=device, weights_only=False)

    # Construire et charger le modèle
    model = build_model(num_classes)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    print(f"Modèle chargé avec succès sur {device}")
    return model


# ─── Prétraitement de l'image ─────────────────────────────────────────────────
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=1),  # Convertir en niveaux de gris
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485], std=[0.229]),
])


# ─── Prédiction ───────────────────────────────────────────────────────────────
def predict(model, image_path, class_names=None, device="cpu"):
    """Prédit la classe d'une image."""
    if not os.path.exists(image_path):
        print(f"Erreur: fichier introuvable -> {image_path}")
        return

    # Charger et prétraiter l'image
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0).to(device)

    # Inférence
    with torch.no_grad():
        outputs = model(tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]
        predicted_class = probabilities.argmax().item()
        confidence = probabilities[predicted_class].item() * 100

    # Afficher les résultats
    print(f"\nImage: {os.path.basename(image_path)}")
    print(f"Prédiction: classe {predicted_class}", end="")
    if class_names:
        print(f" ({class_names[predicted_class]})", end="")
    print(f" - Confiance: {confidence:.1f}%")

    print("\nProbabilités par classe:")
    for i, prob in enumerate(probabilities):
        name = class_names[i] if class_names else f"classe_{i}"
        bar = "█" * int(prob.item() * 20)
        print(f"  {name:12s}: {prob.item()*100:5.1f}% {bar}")

    return predicted_class, confidence


# ─── Afficher l'architecture ──────────────────────────────────────────────────
def show_architecture(model):
    """Affiche un résumé du modèle."""
    print("\n=== Architecture du modèle ===")
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Paramètres totaux    : {total_params:,}")
    print(f"Paramètres entraîn.  : {trainable_params:,}")
    print(f"Couche finale        : {model.fc}")
    print(f"Device               : {DEVICE}")


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Chargement du modèle ResNet Transfer Learning ===\n")

    # Charger le modèle
    model = load_model(MODEL_PATH, num_classes=NUM_CLASSES, device=DEVICE)

    # Afficher l'architecture
    show_architecture(model)

    # Tester avec une image passée en argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        predict(model, image_path, CLASS_NAMES, DEVICE)
    else:
        print("\n=== Usage ===")
        print("  python test_model.py <chemin_vers_image.jpg>")
        print("\nExemple:")
        print("  python test_model.py photo.jpg")
        print("\nLe modèle est prêt ! Passez une image en argument pour prédire sa classe.")
