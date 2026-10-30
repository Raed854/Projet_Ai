# 📖 Guide d'Utilisation - Application Web ECG

## 🎯 Pourquoi 187 valeurs ?

**Réponse courte :** C'est la taille standard d'un battement cardiaque dans le dataset MIT-BIH.

**Explication détaillée :**
- Un battement ECG dure environ **0.8 secondes**
- Échantillonné à **360 Hz** (360 mesures par seconde)
- Puis normalisé et segmenté à **187 points** pour chaque battement
- Cette standardisation permet au modèle d'analyser efficacement

**Solutions pour simplifier :**
1. ✅ **Bouton "Exemple réel"** : Charge automatiquement 187 valeurs
2. ✅ **Upload CSV** : Charger des fichiers de test
3. ✅ **Générateur aléatoire** : Créer des signaux de test
4. ✅ **Historique** : Réutiliser des signaux précédents

---

## 🚀 Démarrage rapide

### Installation
```bash
pip install flask tensorflow pandas numpy
```

### Lancer l'application
```bash
python web_app.py
```

Ouvrir dans le navigateur : **http://localhost:5000**

---

## 📱 Utilisation de l'interface

### Onglet 1 : Saisie manuelle
1. Cliquer sur **"Exemple réel"** pour charger un signal de test
2. Ou coller vos propres valeurs (187 nombres séparés par virgules)
3. Cliquer sur **"Lancer la prédiction"**

### Onglet 2 : Upload fichier CSV
1. Cliquer sur **"📁 Choisir un fichier CSV"**
2. Sélectionner un fichier contenant des signaux ECG
3. Format attendu : 187 colonnes par ligne (avec ou sans en-tête)
4. Le premier signal sera automatiquement chargé

**Exemple de fichier CSV fourni :** `examples.csv`

### Onglet 3 : Signal aléatoire
1. Choisir le type de signal :
   - **Normal** : Simulation d'un battement sain
   - **Anormal** : Simulation avec anomalie
   - **Complètement aléatoire** : Pour tester les limites
2. Cliquer sur **"Générer"**

---

## 📊 Comprendre les résultats

### Classe prédite
Le type de battement détecté par le modèle :
- **N** : Battement normal (le plus fréquent)
- **S** : Battement supraventriculaire (origine oreillettes)
- **V** : Contraction ventriculaire prématurée (arythmie)
- **F** : Fusion de battements
- **Q** : Non classifiable

### Confiance
Probabilité que le modèle a assignée à sa prédiction
- **> 90%** : Très confiant
- **70-90%** : Confiant
- **< 70%** : Incertain

### Graphique du signal
Visualisation du signal ECG analysé
- Axe X : Échantillons (0-187)
- Axe Y : Amplitude normalisée

### Probabilités par classe
Distribution des probabilités pour toutes les classes
- Permet de voir les "deuxièmes choix" du modèle
- Utile si la confiance est faible

---

## 🔧 Fonctionnalités avancées

### Historique 📊
- **Accéder** : Cliquer sur le bouton "📊 Historique"
- **Réutiliser** : Cliquer sur une prédiction passée pour recharger le signal
- **Effacer** : Bouton "Effacer l'historique"
- **Stockage** : Données sauvegardées dans le navigateur (localStorage)
- **Limite** : 10 dernières prédictions

### Informations du modèle
Affichées au bas de la page :
- **Architecture** : CNN 1D
- **Taille d'entrée** : 187 valeurs
- **Dataset** : MIT-BIH Arrhythmia
- **Précision** : Calculée automatiquement si `predictions_ecg.csv` existe

---

## ❓ FAQ

### 1. D'où viennent les 187 valeurs ?
C'est la taille standard des battements dans le dataset MIT-BIH utilisé pour entraîner le modèle.

### 2. Puis-je utiliser moins de valeurs ?
Non, le modèle a été entraîné avec exactement 187 valeurs. Utilisez le générateur aléatoire pour tester rapidement.

### 3. Le fichier CSV ne charge pas
Vérifiez que :
- Le fichier contient exactement 187 colonnes
- Les valeurs sont numériques
- Pas de caractères spéciaux

### 4. La prédiction est lente
C'est normal la première fois (chargement du modèle TensorFlow). Les prédictions suivantes seront plus rapides.

### 5. Puis-je utiliser l'application sans connexion ?
Oui, une fois la page chargée et le modèle en mémoire, l'application fonctionne localement.

### 6. Les résultats sont-ils médicalement valides ?
⚠️ **NON** - C'est un projet pédagogique uniquement. Ne jamais utiliser pour un diagnostic réel.

---

## 🎓 Pour votre présentation/soutenance

### Points forts à mentionner

1. **Solution au problème de saisie**
   - 3 méthodes d'input différentes
   - Upload de fichiers CSV
   - Générateur de signaux

2. **UX/UI moderne**
   - Interface intuitive
   - Design responsive
   - Visualisations claires

3. **Fonctionnalités pratiques**
   - Historique des prédictions
   - Export possible
   - Informations sur le modèle

4. **Aspects techniques**
   - Backend Flask léger
   - Frontend vanilla JS (pas de framework lourd)
   - API REST pour prédictions

### Démonstration suggérée

1. **Intro** (30 sec)
   - Montrer la page d'accueil
   - Expliquer le problème (classification ECG)

2. **Test avec exemple** (1 min)
   - Cliquer "Exemple réel"
   - Lancer prédiction
   - Montrer résultats détaillés

3. **Upload fichier** (1 min)
   - Charger `examples.csv`
   - Montrer la facilité d'utilisation

4. **Générateur** (30 sec)
   - Générer signal aléatoire
   - Tester le modèle

5. **Historique** (30 sec)
   - Afficher l'historique
   - Réutiliser une prédiction

### Questions possibles et réponses

**Q: Pourquoi Flask et pas Streamlit ?**
R: Flask offre plus de contrôle pour une API REST et permet un design plus personnalisé.

**Q: Quelle est la précision du modèle ?**
R: [Vérifier dans predictions_ecg.csv ou mentionner la métrique de votre entraînement]

**Q: Comment gérez-vous les performances ?**
R: Modèle chargé une seule fois au démarrage, prédictions en batch possibles.

**Q: Évolutions futures ?**
R: Voir `AMELIORATIONS.md` - API documentée, mode batch, visualisations avancées.

---

## 📚 Ressources

- **Dataset MIT-BIH** : https://www.physionet.org/content/mitdb/
- **Documentation Flask** : https://flask.palletsprojects.com/
- **TensorFlow.js** (si vous voulez passer au client-side) : https://www.tensorflow.org/js

---

## 🤝 Support

Pour toute question sur l'utilisation ou les améliorations, consultez :
- `README_WEB.md` : Guide de base
- `AMELIORATIONS.md` : Liste complète des améliorations possibles
- Ce fichier : Guide détaillé d'utilisation
