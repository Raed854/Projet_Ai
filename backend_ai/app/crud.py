from sqlalchemy import select
from sqlalchemy.orm import Session

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


def create_user(db: Session, user_data: UserCreate, password_hash: str) -> User:
    user = User(
        prenom=user_data.prenom,
        nom=user_data.nom,
        age=user_data.age,
        telephone=user_data.telephone,
        email=str(user_data.email).lower(),
        password_hash=password_hash,
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalar(statement)


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    statement = select(User).offset(skip).limit(limit).order_by(User.id)
    return list(db.scalars(statement).all())


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def create_alzheimer(db: Session, alzheimer_data: AlzheimerCreate) -> Alzheimer:
    alzheimer = Alzheimer(
        type=alzheimer_data.type,
        user_id=alzheimer_data.user_id,
        confidence=alzheimer_data.confidence,
    )
    db.add(alzheimer)
    db.commit()
    db.refresh(alzheimer)
    return alzheimer


def get_alzheimer(db: Session, alzheimer_id: int) -> Alzheimer | None:
    return db.get(Alzheimer, alzheimer_id)


def get_alzheimers(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Alzheimer]:
    statement = select(Alzheimer).offset(skip).limit(limit).order_by(Alzheimer.id)
    if user_id is not None:
        statement = statement.where(Alzheimer.user_id == user_id)
    return list(db.scalars(statement).all())


def update_alzheimer(
    db: Session,
    alzheimer: Alzheimer,
    alzheimer_data: AlzheimerUpdate,
) -> Alzheimer:
    for field, value in alzheimer_data.model_dump(exclude_unset=True).items():
        setattr(alzheimer, field, value)
    db.commit()
    db.refresh(alzheimer)
    return alzheimer


def delete_alzheimer(db: Session, alzheimer: Alzheimer) -> None:
    db.delete(alzheimer)
    db.commit()


def create_lesion(db: Session, lesion_data: LesionCreate) -> Lesion:
    data = lesion_data.model_dump()
    if data["probabilities"] is not None:
        data["probabilities"] = {
            lesion_type.value: probability
            for lesion_type, probability in data["probabilities"].items()
        }
    lesion = Lesion(**data)
    db.add(lesion)
    db.commit()
    db.refresh(lesion)
    return lesion


def get_lesion(db: Session, lesion_id: int) -> Lesion | None:
    return db.get(Lesion, lesion_id)


def get_lesions(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Lesion]:
    statement = select(Lesion).offset(skip).limit(limit).order_by(Lesion.id)
    if user_id is not None:
        statement = statement.where(Lesion.user_id == user_id)
    return list(db.scalars(statement).all())


def update_lesion(db: Session, lesion: Lesion, lesion_data: LesionUpdate) -> Lesion:
    for field, value in lesion_data.model_dump(exclude_unset=True).items():
        setattr(lesion, field, value)
    db.commit()
    db.refresh(lesion)
    return lesion


def delete_lesion(db: Session, lesion: Lesion) -> None:
    db.delete(lesion)
    db.commit()


def create_dosage(db: Session, dosage_data: DosageCreate) -> Dosage:
    dosage = Dosage(**dosage_data.model_dump(mode="json"))
    db.add(dosage)
    db.commit()
    db.refresh(dosage)
    return dosage


def get_dosage(db: Session, dosage_id: int) -> Dosage | None:
    return db.get(Dosage, dosage_id)


def get_dosages(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Dosage]:
    statement = select(Dosage).offset(skip).limit(limit).order_by(Dosage.id)
    if user_id is not None:
        statement = statement.where(Dosage.user_id == user_id)
    return list(db.scalars(statement).all())


def update_dosage(db: Session, dosage: Dosage, dosage_data: DosageUpdate) -> Dosage:
    for field, value in dosage_data.model_dump(exclude_unset=True).items():
        setattr(dosage, field, value)
    db.commit()
    db.refresh(dosage)
    return dosage


def delete_dosage(db: Session, dosage: Dosage) -> None:
    db.delete(dosage)
    db.commit()


def create_sanguine(db: Session, sanguine_data: SanguineCreate) -> Sanguine:
    sanguine = Sanguine(**sanguine_data.model_dump(mode="json"))
    db.add(sanguine)
    db.commit()
    db.refresh(sanguine)
    return sanguine


def get_sanguine(db: Session, sanguine_id: int) -> Sanguine | None:
    return db.get(Sanguine, sanguine_id)


def get_sanguines(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Sanguine]:
    statement = select(Sanguine).offset(skip).limit(limit).order_by(Sanguine.id)
    if user_id is not None:
        statement = statement.where(Sanguine.user_id == user_id)
    return list(db.scalars(statement).all())


def update_sanguine(db: Session, sanguine: Sanguine, sanguine_data: SanguineUpdate) -> Sanguine:
    for field, value in sanguine_data.model_dump(exclude_unset=True).items():
        setattr(sanguine, field, value)
    db.commit()
    db.refresh(sanguine)
    return sanguine


def delete_sanguine(db: Session, sanguine: Sanguine) -> None:
    db.delete(sanguine)
    db.commit()


def create_cardiaque(db: Session, cardiaque_data: CardiaqueCreate) -> Cardiaque:
    cardiaque = Cardiaque(**cardiaque_data.model_dump(mode="json"))
    db.add(cardiaque)
    db.commit()
    db.refresh(cardiaque)
    return cardiaque


def get_cardiaque(db: Session, cardiaque_id: int) -> Cardiaque | None:
    return db.get(Cardiaque, cardiaque_id)


def get_cardiaques(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Cardiaque]:
    statement = select(Cardiaque).offset(skip).limit(limit).order_by(Cardiaque.id)
    if user_id is not None:
        statement = statement.where(Cardiaque.user_id == user_id)
    return list(db.scalars(statement).all())


def update_cardiaque(
    db: Session,
    cardiaque: Cardiaque,
    cardiaque_data: CardiaqueUpdate,
) -> Cardiaque:
    for field, value in cardiaque_data.model_dump(exclude_unset=True).items():
        setattr(cardiaque, field, value)
    db.commit()
    db.refresh(cardiaque)
    return cardiaque


def delete_cardiaque(db: Session, cardiaque: Cardiaque) -> None:
    db.delete(cardiaque)
    db.commit()


def create_chest(db: Session, chest_data: ChestCreate) -> Chest:
    chest = Chest(**chest_data.model_dump(mode="json"))
    db.add(chest)
    db.commit()
    db.refresh(chest)
    return chest


def get_chest(db: Session, chest_id: int) -> Chest | None:
    return db.get(Chest, chest_id)


def get_chests(
    db: Session,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Chest]:
    statement = select(Chest).offset(skip).limit(limit).order_by(Chest.id)
    if user_id is not None:
        statement = statement.where(Chest.user_id == user_id)
    return list(db.scalars(statement).all())


def update_chest(db: Session, chest: Chest, chest_data: ChestUpdate) -> Chest:
    for field, value in chest_data.model_dump(exclude_unset=True).items():
        setattr(chest, field, value)
    db.commit()
    db.refresh(chest)
    return chest


def delete_chest(db: Session, chest: Chest) -> None:
    db.delete(chest)
    db.commit()
