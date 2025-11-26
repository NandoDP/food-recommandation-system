# app/models.py (exemple structure)
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Dish(Base):
    __tablename__ = "dishes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    meal_type = Column(String)
    cuisine_origin = Column(String)
    
    dish_ingredients = relationship("DishIngredient", back_populates="dish")

class DishIngredient(Base):
    __tablename__ = "dish_ingredients"
    dish_id = Column(UUID(as_uuid=True), ForeignKey("dishes.id"), primary_key=True)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredients.id"), primary_key=True)
    quantity = Column(Float)
    unit = Column(String)
    
    dish = relationship("Dish", back_populates="dish_ingredients")
    ingredient = relationship("Ingredient", back_populates="dish_ingredients")

class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    food_id = Column(UUID(as_uuid=True), ForeignKey("foods.id"))
    
    food = relationship("Food", back_populates="ingredients")
    dish_ingredients = relationship("DishIngredient", back_populates="ingredient")

class Food(Base):
    __tablename__ = "foods"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    local_name = Column(String, nullable=False)
    category = Column(String)
    nutritional_values = Column(JSON)
    glycemic_index = Column(Integer)
    
    ingredients = relationship("Ingredient", back_populates="food")