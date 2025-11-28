from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.sql import func
# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Table, PrimaryKeyConstraint
import uuid
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    # email = Column(String, unique=True, index=True, nullable=False)
    # hashed_password = Column(String, nullable=False)
    last_name = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    birth_date = Column(DateTime)
    gender = Column(Text, nullable=False)
    weight = Column(Integer)
    height = Column(Integer)
    registration_date = Column(DateTime, server_default=func.now())
    language = Column(String, default="fr")

class Disease(Base):
    __tablename__ = "diseases"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    severity_level = Column(String, nullable=True)
    general_recommendations = Column(Text, nullable=True)
    
class Allergen(Base):
    __tablename__ = "allergens"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(Text, nullable=False)
    danger_level = Column(String, nullable=False)
    
# ---------------------------
# Association Tables (M2M)
# ---------------------------
health_profile_diseases = Table(
    "health_profile_diseases",
    Base.metadata,
    Column("health_profile_id", String, ForeignKey("health_profiles.id", ondelete="CASCADE")),
    Column("disease_id", String, ForeignKey("diseases.id", ondelete="CASCADE")),
    PrimaryKeyConstraint("health_profile_id", "disease_id")
)

health_profile_allergens = Table(
    "health_profile_allergens",
    Base.metadata,
    Column("health_profile_id", String, ForeignKey("health_profiles.id", ondelete="CASCADE")),
    Column("allergen_id", String, ForeignKey("allergens.id", ondelete="CASCADE")),
    PrimaryKeyConstraint("health_profile_id", "allergen_id")
)


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(String, primary_key=True, default=( lambda: str(uuid.uuid4()) ))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    physical_activity_level = Column(String, nullable=False)

    user = relationship("User")

    diseases = relationship(
        "Disease",
        secondary="health_profile_diseases",
        # back_populates="health_profiles"
    )

    allergens = relationship(
        "Allergen",
        secondary="health_profile_allergens",
        # back_populates="health_profiles"
    )
