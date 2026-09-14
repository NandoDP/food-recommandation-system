"""
Configuration pytest

Fournit une base SQLite en mémoire et un client FastAPI dont les dépendances
de session sont redirigées vers cette base : les tests ne touchent donc jamais
le PostgreSQL de développement.
"""
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ajouter le répertoire racine au path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from api.schemas.analyze import Base as AnalyzeBase, Dish, DishIngredient, Ingredient, Food
from api.schemas.users import Base as UsersBase, User, Disease, Allergen, HealthProfile


@pytest.fixture
def engine():
    """Moteur SQLite en mémoire, recréé pour chaque test.

    StaticPool + une connexion unique : sans cela chaque session obtiendrait
    sa propre base vide. La portée « fonction » garantit qu'un test qui
    committe ne pollue pas le suivant.
    """
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Les modèles sont répartis sur deux declarative_base distincts
    AnalyzeBase.metadata.create_all(eng)
    UsersBase.metadata.create_all(eng)
    return eng


@pytest.fixture
def db_session(engine):
    """Session isolée : tout est annulé en fin de test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def seeded_db(db_session):
    """Jeu de données minimal : 2 plats, leurs ingrédients, 1 utilisateur."""
    riz = Food(id="f1", local_name="Riz blanc", category="céréale",
               glycemic_index=73, nutritional_values={})
    arachide = Food(id="f2", local_name="Arachide", category="légumineuse",
                    glycemic_index=14, nutritional_values={})
    db_session.add_all([riz, arachide])

    ing_riz = Ingredient(id="i1", name="riz blanc", food_id="f1")
    ing_arachide = Ingredient(id="i2", name="pâte d'arachide", food_id="f2")
    db_session.add_all([ing_riz, ing_arachide])

    thieb = Dish(id="d1", name="Thiéboudienne", meal_type="lunch",
                 cuisine_origin="Sénégal", description="Riz au poisson")
    mafe = Dish(id="d2", name="Mafé cacahuète", meal_type="lunch",
                cuisine_origin="Sénégal", description="Sauce arachide")
    db_session.add_all([thieb, mafe])

    db_session.add_all([
        DishIngredient(dish_id="d1", ingredient_id="i1", quantity=200, unit="g"),
        DishIngredient(dish_id="d2", ingredient_id="i2", quantity=100, unit="g"),
    ])

    db_session.add(User(id="u1", first_name="Test", last_name="User",
                        gender="F", weight=70, height=170))
    db_session.commit()
    return db_session


@pytest.fixture
def client(db_session):
    """TestClient FastAPI branché sur la base de test.

    Chaque module de routes instancie son propre `Database()` ; il faut donc
    surcharger la dépendance de chacun.
    """
    from fastapi.testclient import TestClient

    from api.main import app
    from api.routes import analyze, health_profiles, users

    def override_get_db():
        yield db_session

    for module in (analyze, health_profiles, users):
        app.dependency_overrides[module.db_instance.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
