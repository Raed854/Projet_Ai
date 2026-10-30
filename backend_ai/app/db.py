import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=os.getenv("MYSQL_DATABASE", "ai"),
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True


def migrate_users_table() -> None:
    with engine.begin() as connection:
        columns = {
            row[0]
            for row in connection.execute(text("SHOW COLUMNS FROM users"))
        }

        if "email" not in columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL")
            )

        if "password_hash" not in columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL")
            )

        indexes = connection.execute(text("SHOW INDEX FROM users")).mappings()
        has_email_unique_index = any(
            row["Column_name"] == "email" and row["Non_unique"] == 0
            for row in indexes
        )
        if not has_email_unique_index:
            connection.execute(
                text("CREATE UNIQUE INDEX ix_users_email ON users (email)")
            )


def migrate_alzheimer_table() -> None:
    with engine.begin() as connection:
        columns = {
            row[0]: row[1]
            for row in connection.execute(text("SHOW COLUMNS FROM alzheimer"))
        }

        if "confidence" not in columns:
            connection.execute(
                text("ALTER TABLE alzheimer ADD COLUMN confidence FLOAT NULL")
            )

        # Ancienne valeur 'Impairment' -> classe du modèle 'Moderate Impairment'
        if "'Moderate Impairment'" not in str(columns["type"]):
            connection.execute(
                text(
                    "ALTER TABLE alzheimer MODIFY COLUMN type ENUM("
                    "'No Impairment', 'Very Mild Impairment', 'Mild Impairment', "
                    "'Impairment', 'Moderate Impairment') NOT NULL"
                )
            )
            connection.execute(
                text(
                    "UPDATE alzheimer SET type = 'Moderate Impairment' "
                    "WHERE type = 'Impairment'"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE alzheimer MODIFY COLUMN type ENUM("
                    "'No Impairment', 'Very Mild Impairment', 'Mild Impairment', "
                    "'Moderate Impairment') NOT NULL"
                )
            )


def migrate_lesion_table() -> None:
    with engine.begin() as connection:
        columns = {
            row[0]
            for row in connection.execute(text("SHOW COLUMNS FROM lesion"))
        }

        if "image" not in columns:
            connection.execute(
                text("ALTER TABLE lesion ADD COLUMN image MEDIUMTEXT NULL")
            )

        if "gradcam_image" not in columns:
            connection.execute(
                text("ALTER TABLE lesion ADD COLUMN gradcam_image MEDIUMTEXT NULL")
            )


def migrate_sanguine_table() -> None:
    """Retire l'ancienne table sanguine (version Kaggle / Qwen) avant create_all.

    Vide : supprimée. Avec des lignes : renommée en sanguine_kaggle_old (rien n'est perdu).
    """
    with engine.begin() as connection:
        tables = {row[0] for row in connection.execute(text("SHOW TABLES"))}
        if "sanguine" not in tables:
            return

        columns = {
            row[0]
            for row in connection.execute(text("SHOW COLUMNS FROM sanguine"))
        }
        if "diagnostic" in columns:
            return  # déjà au nouveau format

        nb_lignes = connection.execute(text("SELECT COUNT(*) FROM sanguine")).scalar()
        if nb_lignes == 0:
            connection.execute(text("DROP TABLE sanguine"))
        elif "sanguine_kaggle_old" not in tables:
            connection.execute(text("RENAME TABLE sanguine TO sanguine_kaggle_old"))
        else:
            raise RuntimeError(
                "La table sanguine est à l'ancien format et sanguine_kaggle_old existe déjà : "
                "renommez ou supprimez l'une des deux manuellement."
            )
