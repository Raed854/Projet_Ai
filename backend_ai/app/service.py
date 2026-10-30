from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import bcrypt

from app import crud
from app.models import Alzheimer, Cardiaque, Chest, Dosage, Lesion, Sanguine, User
from app.schemas import (
    AlzheimerCreate,
    AlzheimerUpdate,
    CardiaqueCreate,
    CardiaqueUpdate,
    ChestCreate,
    ChestUpdate,
    DosageCreate,
    DosageUpdate,
    LesionCreate,
    LesionUpdate,
    SanguineCreate,
    SanguineUpdate,
    UserCreate,
    UserUpdate,
)


class UserAlreadyExistsError(Exception):
    pass


def create_user(db: Session, user_data: UserCreate) -> User:
    try:
        password_hash = bcrypt.hashpw(
            user_data.password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        return crud.create_user(db, user_data, password_hash)
    except IntegrityError as error:
        db.rollback()
        raise UserAlreadyExistsError("Ce numéro de téléphone ou e-mail existe déjà.") from error


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = crud.get_user_by_email(db, email)
    if user is None or not bcrypt.checkpw(
        password.encode("utf-8"),
        user.password_hash.encode("utf-8"),
    ):
        return None
    return user


def get_user(db: Session, user_id: int) -> User | None:
    return crud.get_user(db, user_id)


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return crud.get_users(db, skip, limit)


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    try:
        return crud.update_user(db, user, user_data)
    except IntegrityError as error:
        db.rollback()
        raise UserAlreadyExistsError("Ce numéro de téléphone existe déjà.") from error


def delete_user(db: Session, user: User) -> None:
    crud.delete_user(db, user)


def create_alzheimer(db: Session, alzheimer_data: AlzheimerCreate) -> Alzheimer:
    if crud.get_user(db, alzheimer_data.user_id) is None:
        raise ValueError("Utilisateur introuvable.")
    return crud.create_alzheimer(db, alzheimer_data)


def get_alzheimer(db: Session, alzheimer_id: int) -> Alzheimer | None:
    return crud.get_alzheimer(db, alzheimer_id)


def get_alzheimers(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Alzheimer]:
    return crud.get_alzheimers(db, user_id, skip, limit)


def update_alzheimer(
    db: Session,
    alzheimer: Alzheimer,
    alzheimer_data: AlzheimerUpdate,
) -> Alzheimer:
    return crud.update_alzheimer(db, alzheimer, alzheimer_data)


def delete_alzheimer(db: Session, alzheimer: Alzheimer) -> None:
    crud.delete_alzheimer(db, alzheimer)


def create_lesion(db: Session, lesion_data: LesionCreate) -> Lesion:
    if crud.get_user(db, lesion_data.user_id) is None:
        raise ValueError("Utilisateur introuvable.")
    return crud.create_lesion(db, lesion_data)


def get_lesion(db: Session, lesion_id: int) -> Lesion | None:
    return crud.get_lesion(db, lesion_id)


def get_lesions(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Lesion]:
    return crud.get_lesions(db, user_id, skip, limit)


def update_lesion(db: Session, lesion: Lesion, lesion_data: LesionUpdate) -> Lesion:
    return crud.update_lesion(db, lesion, lesion_data)


def delete_lesion(db: Session, lesion: Lesion) -> None:
    crud.delete_lesion(db, lesion)


def create_dosage(db: Session, dosage_data: DosageCreate) -> Dosage:
    if crud.get_user(db, dosage_data.user_id) is None:
        raise ValueError("Utilisateur introuvable.")
    if len(dosage_data.volumes) != len(dosage_data.ph):
        raise ValueError("Les listes 'volumes' et 'ph' doivent avoir la même longueur.")
    return crud.create_dosage(db, dosage_data)


def get_dosage(db: Session, dosage_id: int) -> Dosage | None:
    return crud.get_dosage(db, dosage_id)


def get_dosages(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Dosage]:
    return crud.get_dosages(db, user_id, skip, limit)


def update_dosage(db: Session, dosage: Dosage, dosage_data: DosageUpdate) -> Dosage:
    return crud.update_dosage(db, dosage, dosage_data)


def delete_dosage(db: Session, dosage: Dosage) -> None:
    crud.delete_dosage(db, dosage)


def create_sanguine(db: Session, sanguine_data: SanguineCreate) -> Sanguine:
    if crud.get_user(db, sanguine_data.user_id) is None:
        raise ValueError("Utilisateur introuvable.")
    return crud.create_sanguine(db, sanguine_data)


def get_sanguine(db: Session, sanguine_id: int) -> Sanguine | None:
    return crud.get_sanguine(db, sanguine_id)


def get_sanguines(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Sanguine]:
    return crud.get_sanguines(db, user_id, skip, limit)


def update_sanguine(db: Session, sanguine: Sanguine, sanguine_data: SanguineUpdate) -> Sanguine:
    return crud.update_sanguine(db, sanguine, sanguine_data)


def delete_sanguine(db: Session, sanguine: Sanguine) -> None:
    crud.delete_sanguine(db, sanguine)


def create_cardiaque(db: Session, cardiaque_data: CardiaqueCreate) -> Cardiaque:
    if crud.get_user(db, cardiaque_data.user_id) is None:
        raise ValueError("Utilisateur introuvable.")
    if cardiaque_data.classe_reelle is not None:
        cardiaque_data.prediction_correcte = cardiaque_data.classe == cardiaque_data.classe_reelle
    return crud.create_cardiaque(db, cardiaque_data)


def get_cardiaque(db: Session, cardiaque_id: int) -> Cardiaque | None:
    return crud.get_cardiaque(db, cardiaque_id)


def get_cardiaques(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Cardiaque]:
    return crud.get_cardiaques(db, user_id, skip, limit)


def update_cardiaque(
    db: Session,
    cardiaque: Cardiaque,
    cardiaque_data: CardiaqueUpdate,
) -> Cardiaque:
    # Renseigner la classe réelle recalcule si la prédiction était correcte
    if "classe_reelle" in cardiaque_data.model_fields_set:
        cardiaque.prediction_correcte = (
            None
            if cardiaque_data.classe_reelle is None
            else cardiaque.classe == cardiaque_data.classe_reelle
        )
    return crud.update_cardiaque(db, cardiaque, cardiaque_data)


def delete_cardiaque(db: Session, cardiaque: Cardiaque) -> None:
    crud.delete_cardiaque(db, cardiaque)


def create_chest(db: Session, chest_data: ChestCreate) -> Chest:
    if crud.get_user(db, chest_data.user_id) is None:
        raise ValueError("Utilisateur introuvable.")
    return crud.create_chest(db, chest_data)


def get_chest(db: Session, chest_id: int) -> Chest | None:
    return crud.get_chest(db, chest_id)


def get_chests(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Chest]:
    return crud.get_chests(db, user_id, skip, limit)


def update_chest(db: Session, chest: Chest, chest_data: ChestUpdate) -> Chest:
    return crud.update_chest(db, chest, chest_data)


def delete_chest(db: Session, chest: Chest) -> None:
    crud.delete_chest(db, chest)
