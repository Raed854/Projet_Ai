from enum import Enum

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"


class AlzheimerType(str, Enum):
    NO_IMPAIRMENT = "No Impairment"
    VERY_MILD_IMPAIRMENT = "Very Mild Impairment"
    MILD_IMPAIRMENT = "Mild Impairment"
    MODERATE_IMPAIRMENT = "Moderate Impairment"


class LesionType(str, Enum):
    AKIEC = "akiec"  # Kératose actinique
    BCC = "bcc"  # Carcinome basocellulaire
    BKL = "bkl"  # Kératose bénigne
    DF = "df"  # Dermatofibrome
    MEL = "mel"  # Mélanome
    NV = "nv"  # Naevus
    VASC = "vasc"  # Lésion vasculaire


class VigilanceLevel(str, Enum):
    FAIBLE = "faible"
    MODEREE = "moderee"
    ELEVEE = "elevee"


class DosageType(str, Enum):
    ACIDE_FORT = "acide_fort"
    ACIDE_FAIBLE = "acide_faible"
    BASE_FORTE = "base_forte"
    BASE_FAIBLE = "base_faible"


class DosageDefaut(str, Enum):
    PIC = "pic"  # Pic(s) de pH isolé(s)
    ARRET_PREMATURE = "arret_premature"  # Dosage arrêté avant l'équivalence
    ELECTRODE_DEFAILLANTE = "electrode_defaillante"  # Signal très bruité
    INVERSION = "inversion"  # Évolution du pH incohérente


class SanguineDiagnostic(str, Enum):
    HEALTHY = "Healthy"
    IRON_DEFICIENCY_ANEMIA = "Iron deficiency anemia"
    LEUKEMIA = "Leukemia"
    LEUKEMIA_WITH_THROMBOCYTOPENIA = "Leukemia with thrombocytopenia"
    MACROCYTIC_ANEMIA = "Macrocytic anemia"
    NORMOCYTIC_HYPOCHROMIC_ANEMIA = "Normocytic hypochromic anemia"
    NORMOCYTIC_NORMOCHROMIC_ANEMIA = "Normocytic normochromic anemia"
    OTHER_MICROCYTIC_ANEMIA = "Other microcytic anemia"
    THROMBOCYTOPENIA = "Thrombocytopenia"


class CardiaqueClasse(str, Enum):
    N = "N"  # Battement normal
    S = "S"  # Battement supraventriculaire
    V = "V"  # Contraction ventriculaire prématurée
    F = "F"  # Fusion normale et ventriculaire
    Q = "Q"  # Battement non classifiable


class ChestClasse(str, Enum):
    NORMAL = "NORMAL"
    PNEUMONIA = "PNEUMONIA"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    telephone: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role"),
        nullable=False,
    )
    alzheimers: Mapped[list["Alzheimer"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    lesions: Mapped[list["Lesion"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    dosages: Mapped[list["Dosage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sanguines: Mapped[list["Sanguine"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    cardiaques: Mapped[list["Cardiaque"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    chests: Mapped[list["Chest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Alzheimer(Base):
    __tablename__ = "alzheimer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[AlzheimerType] = mapped_column(
        SqlEnum(
            AlzheimerType,
            name="alzheimer_type",
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    date_creation: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="alzheimers")


class Lesion(Base):
    __tablename__ = "lesion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[LesionType] = mapped_column(
        SqlEnum(
            LesionType,
            name="lesion_type",
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    suspicion_score: Mapped[float] = mapped_column(Float, nullable=False)
    vigilance: Mapped[VigilanceLevel] = mapped_column(
        SqlEnum(
            VigilanceLevel,
            name="vigilance_level",
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        nullable=False,
    )
    probabilities: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    # Images JPEG en data URL base64 (224x224) : image analysée et carte Grad-CAM du modèle
    image: Mapped[str | None] = mapped_column(
        Text().with_variant(MEDIUMTEXT, "mysql"),
        nullable=True,
    )
    gradcam_image: Mapped[str | None] = mapped_column(
        Text().with_variant(MEDIUMTEXT, "mysql"),
        nullable=True,
    )
    date_creation: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="lesions")


def _dosage_type_enum(name: str) -> SqlEnum:
    return SqlEnum(
        DosageType,
        name=name,
        values_callable=lambda enum_type: [item.value for item in enum_type],
    )


class Dosage(Base):
    __tablename__ = "dosage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Entrées : courbe de titrage pH = f(V) et paramètres saisis par l'opérateur
    volumes: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    ph: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    c_titrant: Mapped[float | None] = mapped_column(Float, nullable=True)
    v_prise: Mapped[float | None] = mapped_column(Float, nullable=True)
    type_declare: Mapped[DosageType | None] = mapped_column(
        _dosage_type_enum("dosage_type_declare"),
        nullable=True,
    )

    # Sorties du modèle (service.analyser_courbe)
    veq_derivee: Mapped[float] = mapped_column(Float, nullable=False)
    veq_ia: Mapped[float] = mapped_column(Float, nullable=False)
    veq_ia_incertitude: Mapped[float] = mapped_column(Float, nullable=False)
    veq_retenu: Mapped[float] = mapped_column(Float, nullable=False)
    type_predit: Mapped[DosageType] = mapped_column(
        _dosage_type_enum("dosage_type_predit"),
        nullable=False,
    )
    type_confiance: Mapped[float] = mapped_column(Float, nullable=False)
    probabilites_type: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    score_qualite: Mapped[float] = mapped_column(Float, nullable=False)
    est_anomalie: Mapped[bool] = mapped_column(Boolean, nullable=False)
    defaut_detecte: Mapped[DosageDefaut | None] = mapped_column(
        SqlEnum(
            DosageDefaut,
            name="dosage_defaut",
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        nullable=True,
    )
    pka_estime: Mapped[float | None] = mapped_column(Float, nullable=True)
    concentration: Mapped[float | None] = mapped_column(Float, nullable=True)
    alertes: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    a_revoir: Mapped[bool] = mapped_column(Boolean, nullable=False)
    derivee: Mapped[dict[str, list[float]] | None] = mapped_column(JSON, nullable=True)
    modele_version: Mapped[str] = mapped_column(String(50), nullable=False)

    date_creation: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="dosages")


class Sanguine(Base):
    __tablename__ = "sanguine"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Entrées : paramètres NFS saisis ({"HGB": 8.5, "MCV": 70, ...})
    valeurs: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    # Les 14 paramètres réellement envoyés au modèle (saisis + médianes)
    valeurs_utilisees: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    parametres_completes: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # Sorties du modèle (projet_nfs_cbc/model/cbc_model.joblib)
    diagnostic: Mapped[SanguineDiagnostic] = mapped_column(
        SqlEnum(
            SanguineDiagnostic,
            name="sanguine_diagnostic",
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    probabilities: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    modele: Mapped[str] = mapped_column(String(100), nullable=False)

    date_creation: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="sanguines")


def _cardiaque_classe_enum(name: str) -> SqlEnum:
    return SqlEnum(
        CardiaqueClasse,
        name=name,
        values_callable=lambda enum_type: [item.value for item in enum_type],
    )


class Cardiaque(Base):
    __tablename__ = "cardiaque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Entrée : un battement ECG de 187 valeurs (format MIT-BIH)
    signal: Mapped[list[float]] = mapped_column(JSON, nullable=False)

    # Sorties du modèle CNN 1D (interface_ecg)
    classe: Mapped[CardiaqueClasse] = mapped_column(
        _cardiaque_classe_enum("cardiaque_classe"),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    probabilities: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)

    # Classe réelle si connue (188e colonne d'un CSV MIT-BIH)
    classe_reelle: Mapped[CardiaqueClasse | None] = mapped_column(
        _cardiaque_classe_enum("cardiaque_classe_reelle"),
        nullable=True,
    )
    prediction_correcte: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    modele: Mapped[str] = mapped_column(String(100), nullable=False)

    date_creation: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="cardiaques")


class Chest(Base):
    __tablename__ = "chest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Sorties du modèle DenseNet121 (chest/lung_model.keras)
    classe: Mapped[ChestClasse] = mapped_column(
        SqlEnum(
            ChestClasse,
            name="chest_classe",
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        nullable=False,
    )
    score_pneumonie: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    probabilities: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    seuil: Mapped[float] = mapped_column(Float, nullable=False)
    modele: Mapped[str] = mapped_column(String(100), nullable=False)
    # Radiographie analysée : JPEG 224x224 en data URL base64
    image: Mapped[str | None] = mapped_column(
        Text().with_variant(MEDIUMTEXT, "mysql"),
        nullable=True,
    )

    date_creation: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="chests")
