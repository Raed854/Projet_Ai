from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from datetime import datetime

from typing import Literal

from app.models import (
    AlzheimerType,
    CardiaqueClasse,
    ChestClasse,
    DosageDefaut,
    DosageType,
    LesionType,
    SanguineDiagnostic,
    UserRole,
    VigilanceLevel,
)


class UserBase(BaseModel):
    prenom: str = Field(min_length=1, max_length=100)
    nom: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    telephone: str = Field(min_length=1, max_length=30)
    role: UserRole


class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=150)
    telephone: str | None = Field(default=None, min_length=1, max_length=30)
    role: UserRole | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class AlzheimerCreate(BaseModel):
    type: AlzheimerType
    user_id: int
    confidence: float | None = Field(default=None, ge=0, le=100)


class AlzheimerUpdate(BaseModel):
    type: AlzheimerType | None = None
    confidence: float | None = Field(default=None, ge=0, le=100)


class AlzheimerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: AlzheimerType
    confidence: float | None
    date_creation: datetime
    user_id: int


class LesionCreate(BaseModel):
    type: LesionType
    user_id: int
    confidence: float = Field(ge=0, le=100)
    suspicion_score: float = Field(ge=0, le=100)
    vigilance: VigilanceLevel
    probabilities: dict[LesionType, float] | None = None
    image: str | None = Field(default=None, max_length=5_000_000)
    gradcam_image: str | None = Field(default=None, max_length=5_000_000)


class LesionUpdate(BaseModel):
    type: LesionType | None = None
    vigilance: VigilanceLevel | None = None


class LesionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: LesionType
    confidence: float
    suspicion_score: float
    vigilance: VigilanceLevel
    probabilities: dict[str, float] | None
    image: str | None
    gradcam_image: str | None
    date_creation: datetime
    user_id: int


class DosageAlerte(BaseModel):
    niveau: Literal["critique", "attention"]
    code: str = Field(max_length=50)
    message: str


class DosageDerivee(BaseModel):
    v: list[float]
    d: list[float]


class DosageBase(BaseModel):
    volumes: list[float] = Field(min_length=5)
    ph: list[float] = Field(min_length=5)
    c_titrant: float | None = Field(default=None, gt=0)
    v_prise: float | None = Field(default=None, gt=0)
    type_declare: DosageType | None = None

    veq_derivee: float
    veq_ia: float
    veq_ia_incertitude: float = Field(ge=0)
    veq_retenu: float
    type_predit: DosageType
    type_confiance: float = Field(ge=0, le=1)
    probabilites_type: dict[DosageType, float]
    score_qualite: float = Field(ge=0, le=1)
    est_anomalie: bool
    defaut_detecte: DosageDefaut | None = None
    pka_estime: float | None = None
    concentration: float | None = None
    alertes: list[DosageAlerte] = []
    a_revoir: bool
    derivee: DosageDerivee | None = None
    modele_version: str = Field(min_length=1, max_length=50)


class DosageCreate(DosageBase):
    user_id: int


class DosageUpdate(BaseModel):
    type_declare: DosageType | None = None
    a_revoir: bool | None = None


class DosageRead(DosageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    probabilites_type: dict[str, float]
    date_creation: datetime
    user_id: int


# Paramètres attendus par le modèle NFS / CBC (ordre de cbc_model.joblib)
NFS_PARAMETRES = (
    "WBC", "LYMp", "NEUTp", "LYMn", "NEUTn", "RBC", "HGB",
    "HCT", "MCV", "MCH", "MCHC", "PLT", "PDW", "PCT",
)


def _check_parametres(valeurs: dict[str, float]) -> dict[str, float]:
    inconnus = sorted(set(valeurs) - set(NFS_PARAMETRES))
    if inconnus:
        raise ValueError(f"Paramètres inconnus : {inconnus}. Attendus : {list(NFS_PARAMETRES)}")
    return valeurs


class SanguineBase(BaseModel):
    valeurs: dict[str, float] = Field(min_length=1)
    valeurs_utilisees: dict[str, float] = Field(min_length=len(NFS_PARAMETRES))
    parametres_completes: list[str] = []

    diagnostic: SanguineDiagnostic
    confidence: float = Field(ge=0, le=100)
    probabilities: dict[SanguineDiagnostic, float]
    modele: str = Field(min_length=1, max_length=100)

    _valeurs_connues = field_validator("valeurs", "valeurs_utilisees")(_check_parametres)


class SanguineCreate(SanguineBase):
    user_id: int


class SanguineUpdate(BaseModel):
    diagnostic: SanguineDiagnostic | None = None


class SanguineRead(SanguineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    probabilities: dict[str, float]
    date_creation: datetime
    user_id: int


SIGNAL_LENGTH = 187


class CardiaqueBase(BaseModel):
    signal: list[float] = Field(min_length=SIGNAL_LENGTH, max_length=SIGNAL_LENGTH)
    classe: CardiaqueClasse
    confidence: float = Field(ge=0, le=100)
    probabilities: dict[CardiaqueClasse, float]
    classe_reelle: CardiaqueClasse | None = None
    prediction_correcte: bool | None = None
    modele: str = Field(min_length=1, max_length=100)


class CardiaqueCreate(CardiaqueBase):
    user_id: int


class CardiaqueUpdate(BaseModel):
    classe_reelle: CardiaqueClasse | None = None


class CardiaqueRead(CardiaqueBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    probabilities: dict[str, float]
    date_creation: datetime
    user_id: int


class ChestBase(BaseModel):
    classe: ChestClasse
    score_pneumonie: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    probabilities: dict[ChestClasse, float]
    seuil: float = Field(ge=0, le=100)
    modele: str = Field(min_length=1, max_length=100)
    image: str | None = Field(default=None, max_length=5_000_000)


class ChestCreate(ChestBase):
    user_id: int


class ChestUpdate(BaseModel):
    classe: ChestClasse | None = None


class ChestRead(ChestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    probabilities: dict[str, float]
    date_creation: datetime
    user_id: int
