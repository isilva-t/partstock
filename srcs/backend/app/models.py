from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class Make(Base):
    __tablename__ = "makes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    models = relationship("Model", back_populates="make")


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    make_id = Column(Integer, ForeignKey("makes.id"), nullable=False)
    name = Column(String(100), nullable=False)
    start_year = Column(Integer)
    end_year = Column(Integer)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    make = relationship("Make", back_populates="models")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(15), nullable=False, unique=True)

    sub_categories = relationship("SubCategory", back_populates="category")


class SubCategory(Base):
    __tablename__ = "sub_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(15), nullable=False, unique=True)
    ref_example = Column(String(1), nullable=False, unique=True)

    category = relationship("Category", back_populates="sub_categories")
    components = relationship("Component", back_populates="sub_category")


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    sub_category_id = Column(Integer, ForeignKey(
        "sub_categories.id"), nullable=False)
    name = Column(String(60), nullable=False, unique=True)
    ref = Column(String(2), nullable=False, unique=True)

    sub_category = relationship("SubCategory", back_populates="components")
