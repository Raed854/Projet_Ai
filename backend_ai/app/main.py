from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import service
from app.db import (
    Base,
    engine,
    get_db,
    migrate_alzheimer_table,
    migrate_lesion_table,
    migrate_sanguine_table,
    migrate_users_table,
)
from app.schemas import (
    AlzheimerCreate,
    AlzheimerRead,
    AlzheimerUpdate,
    CardiaqueCreate,
    CardiaqueRead,
    CardiaqueUpdate,
    ChestCreate,
    ChestRead,
    ChestUpdate,
    DosageCreate,
    DosageRead,
    DosageUpdate,
    LesionCreate,
    LesionRead,
    LesionUpdate,
    LoginRequest,
    SanguineCreate,
    SanguineRead,
    SanguineUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)

app = FastAPI(title="Backend AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables() -> None:
    migrate_sanguine_table()
    Base.metadata.create_all(bind=engine)
    migrate_users_table()
    migrate_alzheimer_table()
    migrate_lesion_table()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "API opérationnelle"}


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        return service.create_user(db, user_data)
    except service.UserAlreadyExistsError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        return service.create_user(db, user_data)
    except service.UserAlreadyExistsError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@app.post("/auth/login", response_model=UserRead)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, str(credentials.email), credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou mot de passe incorrect.",
        )
    return user


@app.get("/users", response_model=list[UserRead])
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_users(db, skip, limit)


@app.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    return user


@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
):
    user = service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    try:
        return service.update_user(db, user, user_data)
    except service.UserAlreadyExistsError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    user = service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    service.delete_user(db, user)


@app.post(
    "/alzheimers",
    response_model=AlzheimerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_alzheimer(
    alzheimer_data: AlzheimerCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_alzheimer(db, alzheimer_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@app.get("/alzheimers", response_model=list[AlzheimerRead])
def list_alzheimers(
    user_id: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_alzheimers(db, user_id, skip, limit)


@app.get("/alzheimers/{alzheimer_id}", response_model=AlzheimerRead)
def read_alzheimer(alzheimer_id: int, db: Session = Depends(get_db)):
    alzheimer = service.get_alzheimer(db, alzheimer_id)
    if alzheimer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Évaluation Alzheimer introuvable.",
        )
    return alzheimer


@app.patch("/alzheimers/{alzheimer_id}", response_model=AlzheimerRead)
def update_alzheimer(
    alzheimer_id: int,
    alzheimer_data: AlzheimerUpdate,
    db: Session = Depends(get_db),
):
    alzheimer = service.get_alzheimer(db, alzheimer_id)
    if alzheimer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Évaluation Alzheimer introuvable.",
        )
    return service.update_alzheimer(db, alzheimer, alzheimer_data)


@app.delete("/alzheimers/{alzheimer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alzheimer(alzheimer_id: int, db: Session = Depends(get_db)) -> None:
    alzheimer = service.get_alzheimer(db, alzheimer_id)
    if alzheimer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Évaluation Alzheimer introuvable.",
        )
    service.delete_alzheimer(db, alzheimer)


@app.post(
    "/lesions",
    response_model=LesionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lesion(
    lesion_data: LesionCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_lesion(db, lesion_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@app.get("/lesions", response_model=list[LesionRead])
def list_lesions(
    user_id: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_lesions(db, user_id, skip, limit)


@app.get("/lesions/{lesion_id}", response_model=LesionRead)
def read_lesion(lesion_id: int, db: Session = Depends(get_db)):
    lesion = service.get_lesion(db, lesion_id)
    if lesion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse de lésion introuvable.",
        )
    return lesion


@app.patch("/lesions/{lesion_id}", response_model=LesionRead)
def update_lesion(
    lesion_id: int,
    lesion_data: LesionUpdate,
    db: Session = Depends(get_db),
):
    lesion = service.get_lesion(db, lesion_id)
    if lesion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse de lésion introuvable.",
        )
    return service.update_lesion(db, lesion, lesion_data)


@app.delete("/lesions/{lesion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesion(lesion_id: int, db: Session = Depends(get_db)) -> None:
    lesion = service.get_lesion(db, lesion_id)
    if lesion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse de lésion introuvable.",
        )
    service.delete_lesion(db, lesion)


@app.post(
    "/dosages",
    response_model=DosageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dosage(
    dosage_data: DosageCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_dosage(db, dosage_data)
    except ValueError as error:
        detail = str(error)
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if detail == "Utilisateur introuvable."
                else status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=detail,
        ) from error


@app.get("/dosages", response_model=list[DosageRead])
def list_dosages(
    user_id: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_dosages(db, user_id, skip, limit)


@app.get("/dosages/{dosage_id}", response_model=DosageRead)
def read_dosage(dosage_id: int, db: Session = Depends(get_db)):
    dosage = service.get_dosage(db, dosage_id)
    if dosage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dosage introuvable.",
        )
    return dosage


@app.patch("/dosages/{dosage_id}", response_model=DosageRead)
def update_dosage(
    dosage_id: int,
    dosage_data: DosageUpdate,
    db: Session = Depends(get_db),
):
    dosage = service.get_dosage(db, dosage_id)
    if dosage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dosage introuvable.",
        )
    return service.update_dosage(db, dosage, dosage_data)


@app.delete("/dosages/{dosage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dosage(dosage_id: int, db: Session = Depends(get_db)) -> None:
    dosage = service.get_dosage(db, dosage_id)
    if dosage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dosage introuvable.",
        )
    service.delete_dosage(db, dosage)


@app.post(
    "/sanguines",
    response_model=SanguineRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sanguine(
    sanguine_data: SanguineCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_sanguine(db, sanguine_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@app.get("/sanguines", response_model=list[SanguineRead])
def list_sanguines(
    user_id: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_sanguines(db, user_id, skip, limit)


@app.get("/sanguines/{sanguine_id}", response_model=SanguineRead)
def read_sanguine(sanguine_id: int, db: Session = Depends(get_db)):
    sanguine = service.get_sanguine(db, sanguine_id)
    if sanguine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse sanguine introuvable.",
        )
    return sanguine


@app.patch("/sanguines/{sanguine_id}", response_model=SanguineRead)
def update_sanguine(
    sanguine_id: int,
    sanguine_data: SanguineUpdate,
    db: Session = Depends(get_db),
):
    sanguine = service.get_sanguine(db, sanguine_id)
    if sanguine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse sanguine introuvable.",
        )
    return service.update_sanguine(db, sanguine, sanguine_data)


@app.delete("/sanguines/{sanguine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sanguine(sanguine_id: int, db: Session = Depends(get_db)) -> None:
    sanguine = service.get_sanguine(db, sanguine_id)
    if sanguine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse sanguine introuvable.",
        )
    service.delete_sanguine(db, sanguine)


@app.post(
    "/cardiaques",
    response_model=CardiaqueRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cardiaque(
    cardiaque_data: CardiaqueCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_cardiaque(db, cardiaque_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@app.get("/cardiaques", response_model=list[CardiaqueRead])
def list_cardiaques(
    user_id: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_cardiaques(db, user_id, skip, limit)


@app.get("/cardiaques/{cardiaque_id}", response_model=CardiaqueRead)
def read_cardiaque(cardiaque_id: int, db: Session = Depends(get_db)):
    cardiaque = service.get_cardiaque(db, cardiaque_id)
    if cardiaque is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse cardiaque introuvable.",
        )
    return cardiaque


@app.patch("/cardiaques/{cardiaque_id}", response_model=CardiaqueRead)
def update_cardiaque(
    cardiaque_id: int,
    cardiaque_data: CardiaqueUpdate,
    db: Session = Depends(get_db),
):
    cardiaque = service.get_cardiaque(db, cardiaque_id)
    if cardiaque is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse cardiaque introuvable.",
        )
    return service.update_cardiaque(db, cardiaque, cardiaque_data)


@app.delete("/cardiaques/{cardiaque_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cardiaque(cardiaque_id: int, db: Session = Depends(get_db)) -> None:
    cardiaque = service.get_cardiaque(db, cardiaque_id)
    if cardiaque is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse cardiaque introuvable.",
        )
    service.delete_cardiaque(db, cardiaque)


@app.post(
    "/chests",
    response_model=ChestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_chest(
    chest_data: ChestCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_chest(db, chest_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@app.get("/chests", response_model=list[ChestRead])
def list_chests(
    user_id: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_chests(db, user_id, skip, limit)


@app.get("/chests/{chest_id}", response_model=ChestRead)
def read_chest(chest_id: int, db: Session = Depends(get_db)):
    chest = service.get_chest(db, chest_id)
    if chest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse thoracique introuvable.",
        )
    return chest


@app.patch("/chests/{chest_id}", response_model=ChestRead)
def update_chest(
    chest_id: int,
    chest_data: ChestUpdate,
    db: Session = Depends(get_db),
):
    chest = service.get_chest(db, chest_id)
    if chest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse thoracique introuvable.",
        )
    return service.update_chest(db, chest, chest_data)


@app.delete("/chests/{chest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chest(chest_id: int, db: Session = Depends(get_db)) -> None:
    chest = service.get_chest(db, chest_id)
    if chest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse thoracique introuvable.",
        )
    service.delete_chest(db, chest)
