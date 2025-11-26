import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import traceback
from api.core.config import settings


class Database:
    """Classe utilitaire pour gérer la connexion à une base Postgres locale.

    Exemple d'utilisation:
        db = Database()  # récupère l'URL depuis DATABASE_URL ou utilise la valeur par défaut
        with db.get_db() as session:
            ...
    """

    def __init__(self, database_url: Optional[str] = None):
        # Priorité à la variable d'environnement DATABASE_URL si fournie
        self.database_url = database_url or settings.DATABASE_URL

        # Configuration de l'engine
        # Force client encoding to UTF8 to avoid Unicode decode errors when the server
        # responds with a different encoding. If your database is not UTF8, consider
        # changing the server encoding to UTF8 or adjusting this option.
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"options": "-c client_encoding=UTF8"},
        )

        # sessionmaker configuré
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Base pour déclarer les modèles
        self.Base = declarative_base()

    def get_db(self) -> Generator[Session, None, None]:
        """Dépendance yield-compatible pour FastAPI.

        Usage dans FastAPI:
            with Depends(db_instance.get_db):
                ...

        Pour usage manuel en script, utilisez `db.SessionLocal()`.
        """
        db: Session = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_connection(self) -> bool:
        """Teste la connexion à la base. Retourne True si OK, False sinon."""
        try:
            with self.engine.connect() as connection:
                # Use exec_driver_sql for raw SQL with SQLAlchemy 2.x
                result = connection.exec_driver_sql("SELECT 1")
                print("Database connection successful:", result.fetchone())
            return True
        except Exception as e:
            print("Database connection failed:", e)
            traceback.print_exc()
            return False


if __name__ == "__main__":
    db = Database()
    db.test_connection()