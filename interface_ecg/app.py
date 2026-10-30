import os
import numpy as np
import pandas as pd
import streamlit as st
import tensorflow as tf
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

st.set_page_config(page_title="Analyse ECG", page_icon="❤️", layout="wide")

st.markdown(
    """
    <style>
    .main-title {text-align:center; font-size:42px; font-weight:bold;
                 color:#c1121f; margin-bottom:5px;}
    .subtitle {text-align:center; font-size:18px; color:#64748b;
               margin-bottom:30px;}
    </style>
    """,
    unsafe_allow_html=True
)

MODEL_PATH = "ecg_cnn_final.keras"
BEST_MODEL_PATH = "best_ecg_cnn.keras"
PREDICTIONS_PATH = "predictions_ecg.csv"
SIGNAL_LENGTH = 187

CLASS_NAMES = {
    0: "N - Battement normal",
    1: "S - Battement supraventriculaire",
    2: "V - Contraction ventriculaire prématurée",
    3: "F - Fusion normale et ventriculaire",
    4: "Q - Battement non classifiable",
}


# ------------------------------------------------------------
# Chargement
# ------------------------------------------------------------

@st.cache_resource
def load_model():
    if os.path.exists(MODEL_PATH):
        path = MODEL_PATH
    elif os.path.exists(BEST_MODEL_PATH):
        path = BEST_MODEL_PATH
    else:
        raise FileNotFoundError("Aucun fichier de modèle .keras trouvé.")
    return tf.keras.models.load_model(path, compile=False), path


@st.cache_data
def load_predictions():
    if not os.path.exists(PREDICTIONS_PATH):
        return None
    return pd.read_csv(PREDICTIONS_PATH)


try:
    model, selected_model_path = load_model()
except Exception as error:
    st.error("Erreur pendant le chargement du modèle.")
    st.code(str(error))
    st.stop()

predictions_df = load_predictions()


# ------------------------------------------------------------
# Fonctions de prédiction
# ------------------------------------------------------------

def prepare_signal(signal):
    """Adapte le signal à la forme d'entrée du modèle."""
    x = np.asarray(signal, dtype="float32")
    if len(model.input_shape) == 3:
        return x.reshape(1, -1, 1)
    return x.reshape(1, -1)


def predict_signal(signal):
    return model.predict(prepare_signal(signal), verbose=0)[0]


def show_prediction(signal, probs, true_class=None):
    predicted = int(np.argmax(probs))

    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(signal, color="#c1121f", linewidth=1.5)
    ax.set_title("Signal ECG analysé")
    ax.set_xlabel("Échantillon")
    ax.set_ylabel("Amplitude")
    ax.grid(alpha=0.2)
    st.pyplot(fig)
    plt.close(fig)

    c1, c2, c3 = st.columns(3)
    c1.metric("Classe prédite", CLASS_NAMES.get(predicted, str(predicted)))
    c2.metric("Confiance", f"{probs[predicted] * 100:.2f} %")
    if true_class is not None:
        true_class = int(true_class)
        c3.metric(
            "Classe réelle",
            CLASS_NAMES.get(true_class, str(true_class)),
            "✅ Correct" if predicted == true_class else "❌ Incorrect",
        )

    st.subheader("Probabilités par classe")
    st.bar_chart(
        pd.Series(probs, index=[CLASS_NAMES.get(i, str(i)) for i in range(len(probs))])
    )


def parse_text_signal(text):
    values = [float(v) for v in text.replace(",", " ").replace(";", " ").split()]
    return values


# ------------------------------------------------------------
# Titre et navigation
# ------------------------------------------------------------

st.markdown(
    '<div class="main-title">❤️ Analyse du rythme cardiaque</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Classification de battements ECG avec un CNN 1D</div>',
    unsafe_allow_html=True
)

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Sélectionne une page",
    ["Tester mon signal", "Accueil", "Modèle", "Résultats"],
)
st.sidebar.success(f"Modèle chargé : {selected_model_path}")
st.sidebar.warning(
    "Application pédagogique uniquement. "
    "Les résultats ne constituent pas un diagnostic médical."
)


# ------------------------------------------------------------
# Page : Tester mon signal (saisie utilisateur -> modèle)
# ------------------------------------------------------------

if page == "Tester mon signal":

    st.header("Saisis ton signal ECG")
    st.markdown(
        f"Le modèle attend **{SIGNAL_LENGTH} valeurs** (un battement). "
        "Choisis comment fournir les données."
    )

    mode = st.radio(
        "Méthode de saisie",
        ["Coller des valeurs", "Importer un fichier CSV"],
        horizontal=True,
    )

    if mode == "Coller des valeurs":

        text = st.text_area(
            f"{SIGNAL_LENGTH} valeurs séparées par des virgules, espaces ou retours à la ligne",
            height=180,
            placeholder="0.98, 0.91, 0.72, 0.46, ...",
        )

        if st.button("Lancer la prédiction", type="primary"):
            try:
                values = parse_text_signal(text)
            except ValueError:
                st.error("Valeurs invalides : n'utilise que des nombres.")
                st.stop()

            if len(values) != SIGNAL_LENGTH:
                st.error(f"{len(values)} valeurs reçues, {SIGNAL_LENGTH} attendues.")
            else:
                show_prediction(values, predict_signal(values))

    else:

        uploaded = st.file_uploader("Fichier CSV (sans en-tête)", type=["csv"])
        st.caption(
            "Chaque ligne = un battement : 187 valeurs, "
            "plus éventuellement la classe réelle en 188e colonne "
            "(format du dataset MIT-BIH de Kaggle)."
        )

        if uploaded is not None:
            data = pd.read_csv(uploaded, header=None, nrows=5000)
            data = data.apply(pd.to_numeric, errors="coerce").dropna()

            if data.shape[1] not in (SIGNAL_LENGTH, SIGNAL_LENGTH + 1):
                st.error(
                    f"{data.shape[1]} colonnes détectées, "
                    f"{SIGNAL_LENGTH} ou {SIGNAL_LENGTH + 1} attendues."
                )
            else:
                has_label = data.shape[1] == SIGNAL_LENGTH + 1
                st.success(f"{len(data)} signaux chargés.")

                idx = st.number_input(
                    "Numéro du signal à analyser",
                    min_value=0,
                    max_value=len(data) - 1,
                    value=0,
                    step=1,
                )
                row = data.iloc[int(idx)].values
                signal = row[:SIGNAL_LENGTH]
                true_class = row[SIGNAL_LENGTH] if has_label else None

                if st.button("Lancer la prédiction", type="primary"):
                    show_prediction(signal, predict_signal(signal), true_class)

                with st.expander("Prédire tous les signaux du fichier"):
                    if st.button("Analyser tout le fichier"):
                        X = data.iloc[:, :SIGNAL_LENGTH].values.astype("float32")
                        if len(model.input_shape) == 3:
                            X = X[..., np.newaxis]
                        probs_all = model.predict(X, batch_size=256, verbose=0)
                        out = pd.DataFrame({
                            "classe_predite": probs_all.argmax(axis=1),
                            "confiance": probs_all.max(axis=1),
                        })
                        if has_label:
                            out.insert(0, "classe_reelle", data.iloc[:, SIGNAL_LENGTH].astype(int).values)
                            acc = (out["classe_reelle"] == out["classe_predite"]).mean()
                            st.metric("Accuracy", f"{acc * 100:.2f} %")
                        st.dataframe(out, use_container_width=True)
                        st.download_button(
                            "Télécharger les résultats (CSV)",
                            out.to_csv(index=False).encode("utf-8"),
                            "resultats_ecg.csv",
                            "text/csv",
                        )


# ------------------------------------------------------------
# Page : Accueil
# ------------------------------------------------------------

elif page == "Accueil":

    st.header("Présentation du projet")
    st.markdown(
        f"""
        Cette application utilise un **CNN 1D** entraîné pour classifier des
        battements cardiaques. Il reçoit un signal de **{SIGNAL_LENGTH} valeurs**
        et retourne une prédiction parmi **5 classes**.

        Va sur la page **Tester mon signal** pour saisir tes propres données.
        """
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Type du modèle", "CNN 1D")
    c2.metric("Taille du signal", f"{SIGNAL_LENGTH} valeurs")
    c3.metric("Nombre de classes", "5")

    st.subheader("Classes ECG")
    st.dataframe(
        pd.DataFrame({
            "Numéro": list(CLASS_NAMES.keys()),
            "Signification": list(CLASS_NAMES.values()),
        }),
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------
# Page : Modèle
# ------------------------------------------------------------

elif page == "Modèle":

    st.header("Informations du modèle")
    c1, c2, c3 = st.columns(3)
    c1.metric("Nombre de couches", len(model.layers))
    c2.metric("Nombre de paramètres", f"{model.count_params():,}".replace(",", " "))
    c3.metric("Fichier chargé", selected_model_path)

    st.write("Forme d'entrée :", model.input_shape)
    st.write("Forme de sortie :", model.output_shape)

    lines = []
    model.summary(print_fn=lambda line: lines.append(line))
    st.code("\n".join(lines), language="text")


# ------------------------------------------------------------
# Page : Résultats (prédictions déjà calculées sur Kaggle)
# ------------------------------------------------------------

elif page == "Résultats":

    st.header("Résultats enregistrés (test Kaggle)")

    if predictions_df is None:
        st.warning("Le fichier predictions_ecg.csv est introuvable.")
        st.stop()

    st.success(f"{len(predictions_df)} prédictions chargées.")
    st.dataframe(predictions_df.head(30), use_container_width=True)

    real = pd.to_numeric(predictions_df["classe_reelle"], errors="coerce")
    pred = pd.to_numeric(predictions_df["classe_predite"], errors="coerce")
    ok = real.notna() & pred.notna()

    c1, c2, c3 = st.columns(3)
    c1.metric("Nombre de prédictions", len(predictions_df))
    c2.metric("Accuracy", f"{(real[ok] == pred[ok]).mean() * 100:.2f} %")
    c3.metric(
        "Confiance moyenne",
        f"{pd.to_numeric(predictions_df['confiance'], errors='coerce').mean() * 100:.2f} %",
    )

    st.subheader("Matrice de confusion")
    cm = pd.crosstab(
        real[ok].astype(int), pred[ok].astype(int),
        rownames=["Classe réelle"], colnames=["Classe prédite"],
    )
    st.dataframe(cm, use_container_width=True)

    st.subheader("Distribution de la confiance")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(
        pd.to_numeric(predictions_df["confiance"], errors="coerce").dropna(),
        bins=20, color="#2563eb", edgecolor="white",
    )
    ax.set_xlabel("Confiance")
    ax.set_ylabel("Nombre de prédictions")
    ax.grid(alpha=0.2)
    st.pyplot(fig)
    plt.close(fig)


st.markdown("---")
st.caption("Projet académique de classification des battements ECG. Résultats expérimentaux.")