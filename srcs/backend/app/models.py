from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
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


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    component_ref = Column(String(2), ForeignKey(
        "components.ref"), nullable=False)  # Like "CA" or "ME"
    sku_id = Column(Integer, nullable=False)
    # concatenated component_ref + sku_id
    sku = Column(String(10), nullable=False, unique=True)
    title = Column(String(70), nullable=False)
    description = Column(String(150), nullable=False)
    reference_price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    component = relationship("Component")
    instances = relationship("Instance", back_populates="product")
    photos = relationship("ProductPhoto", back_populates="product")
    compatibilities = relationship(
        "ProductCompatibility", back_populates="product")

    # Unique constraint for component_ref + sku_id combination
    __table_args__ = (
        UniqueConstraint('component_ref', 'sku_id', name='unique_product_sku'),
    )


class Instance(Base):
    __tablename__ = "instances"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    year_month = Column(String(3), nullable=False)  # Like "25A" or "25L"
    sku_id = Column(Integer, nullable=False)
    # concatenated year_month + sku_id
    sku = Column(String(10), nullable=False, unique=True)
    alternative_sku = Column(String(100))
    selling_price = Column(Integer, nullable=False)
    km = Column(Integer, nullable=True)  # Motor kilometers
    observations = Column(String(150))
    # active|sold|incomplete|consume
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="instances")
    photos = relationship("InstancePhoto", back_populates="instance")

    # Unique constraint for year_month + sku_id combination
    __table_args__ = (
        UniqueConstraint('year_month', 'sku_id', name='unique_instance_sku'),
    )


class ProductCompatibility(Base):
    __tablename__ = "product_compatibility"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="compatibilities")
    model = relationship("Model")

    # Unique constraint to prevent duplicate compatibility entries
    __table_args__ = (
        UniqueConstraint('product_id', 'model_id',
                         name='unique_product_model'),
    )


class ProductPhoto(Base):
    __tablename__ = "product_photos"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    filename = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="photos")


class InstancePhoto(Base):
    __tablename__ = "instance_photos"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    filename = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    instance = relationship("Instance", back_populates="photos")
