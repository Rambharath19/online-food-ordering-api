from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Boolean,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="CUSTOMER")

    orders = relationship("Order", back_populates="user")

    cart = relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    restaurant = relationship("Restaurant", back_populates="owner", uselist=False)

    addresses = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# ============================================================
# CATEGORY MODEL
# ============================================================

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    food_items = relationship(
        "FoodItem",
        back_populates="category_ref",
    )


# ============================================================
# RESTAURANT MODEL
# ============================================================

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    owner = relationship("User", back_populates="restaurant")
    food_items = relationship("FoodItem", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")


# ============================================================
# FOOD ITEM MODEL
# ============================================================

class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    price = Column(Float, nullable=False)

    # Retain the existing category text field
    category = Column(String(100), nullable=True)

    # Link to the categories table
    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True,
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
    )

    is_available = Column(Boolean, default=True, nullable=False)

    restaurant = relationship("Restaurant", back_populates="food_items")

    # Correct relationship name for Category.food_items
    category_ref = relationship(
        "Category",
        back_populates="food_items",
    )

    cart_items = relationship("CartItem", back_populates="food_item")
    order_items = relationship("OrderItem", back_populates="food_item")

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_food_price_nonnegative"),
    )


# ============================================================
# ADDRESS MODEL
# ============================================================

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    recipient_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    address_line = Column(String(300), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="address")


# ============================================================
# CART MODEL
# ============================================================

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=True,
    )

    user = relationship("User", back_populates="cart")
    restaurant = relationship("Restaurant")

    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
    )


# ============================================================
# CART ITEM MODEL
# ============================================================

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)

    cart_id = Column(
        Integer,
        ForeignKey("carts.id"),
        nullable=False,
    )

    food_item_id = Column(
        Integer,
        ForeignKey("food_items.id"),
        nullable=False,
    )

    quantity = Column(Integer, nullable=False)

    cart = relationship("Cart", back_populates="items")
    food_item = relationship("FoodItem", back_populates="cart_items")

    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "food_item_id",
            name="uq_cart_food_item",
        ),
        CheckConstraint(
            "quantity > 0",
            name="check_cart_quantity_positive",
        ),
    )


# ============================================================
# ORDER MODEL
# ============================================================

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
    )

    address_id = Column(
        Integer,
        ForeignKey("addresses.id"),
        nullable=True,
    )

    total_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    address = relationship("Address", back_populates="orders")

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="check_order_total_nonnegative",
        ),
    )


# ============================================================
# ORDER ITEM MODEL
# ============================================================

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
    )

    food_item_id = Column(
        Integer,
        ForeignKey("food_items.id"),
        nullable=False,
    )

    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    food_item = relationship("FoodItem", back_populates="order_items")

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="check_order_quantity_positive",
        ),
        CheckConstraint(
            "price >= 0",
            name="check_order_item_price_nonnegative",
        ),
    )