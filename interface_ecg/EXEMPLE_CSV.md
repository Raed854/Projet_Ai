# 📝 Comment créer un fichier CSV pour tester votre modèle ECG

## Méthode 1 : Avec Excel / Google Sheets

1. Ouvrez Excel ou Google Sheets
2. Mettez 187 valeurs sur **une seule ligne** (dans 187 colonnes)
3. Chaque ligne = un battement ECG
4. Enregistrez sous → Format CSV

**Exemple dans Excel :**
```
| A    | B    | C    | D    | ... | GG   |
|------|------|------|------|-----|------|
| 0.98 | 0.91 | 0.72 | 0.46 | ... | -0.26|
| 0.95 | 0.88 | 0.75 | 0.58 | ... | 0.55 |
```

## Méthode 2 : Avec le Bloc-notes (Notepad)

1. Ouvrir le Bloc-notes
2. Copier-coller des valeurs séparées par des virgules
3. Enregistrer avec l'extension `.csv`

**Exemple :**
```
0.98,0.91,0.72,0.46,...,-0.26
0.95,0.88,0.75,0.58,...,0.55
```

## Méthode 3 : Utiliser votre fichier Kaggle

Si vous avez déjà utilisé un dataset Kaggle (MIT-BIH), c'est déjà au format CSV !

Le fichier ressemble à :
```
mitbih_train.csv
mitbih_test.csv
```

Chaque ligne contient 187 ou 188 colonnes :
- **187 colonnes** = signal ECG seulement
- **188 colonnes** = signal ECG + classe réelle (0,1,2,3,4)

## 🎯 Tester avec l'exemple fourni

J'ai créé un fichier **examples.csv** dans votre projet avec 3 signaux de test.

### Pour l'utiliser dans l'application :

1. Lancer l'application web : `python web_app.py`
2. Aller sur l'onglet **"Upload fichier CSV"**
3. Cliquer sur **"📁 Choisir un fichier CSV"**
4. Sélectionner **examples.csv**
5. Cliquer sur **"Lancer la prédiction"**

## 📊 Format du fichier CSV

### Format minimal (signal seulement) :
```csv
0.98,0.91,0.72,0.46,0.18,-0.12,...
0.95,0.88,0.75,0.58,0.38,0.16,...
```

### Format complet (avec classe réelle) :
```csv
0.98,0.91,0.72,0.46,0.18,-0.12,...,0
0.95,0.88,0.75,0.58,0.38,0.16,...,1
```

Le dernier chiffre (0, 1, 2, 3, 4) indique la vraie classe du battement.

## ✅ Vérification rapide de votre CSV

**Un bon fichier CSV pour ce projet :**
- ✅ Chaque ligne = 187 valeurs (ou 188 avec la classe)
- ✅ Valeurs séparées par des virgules
- ✅ Valeurs numériques (pas de texte)
- ✅ Pas d'espaces inutiles
- ✅ Extension `.csv`

**Erreurs courantes :**
- ❌ Moins de 187 valeurs par ligne
- ❌ Séparateur différent (point-virgule, tabulation)
- ❌ En-tête avec du texte
- ❌ Valeurs manquantes

## 🔧 Si votre CSV ne fonctionne pas

Vérifiez dans le Bloc-notes que ça ressemble à :
```
0.98,0.91,0.72,...
```

Et PAS à :
```
Signal ECG 1
0.98;0.91;0.72;...
```

## 💡 Astuce

Vous pouvez aussi simplement cliquer sur **"Exemple réel"** dans l'application pour tester sans créer de fichier CSV !
