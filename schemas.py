from datetime import datetime
from typing import Optional, Literal

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# USER
# ============================================================

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# RESTAURANT OWNER
# ============================================================

class OwnerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class OwnerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# LOGIN
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================
# RESTAURANT
# ============================================================

class RestaurantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    location: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    owner_id: int = Field(..., gt=0)


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)


class RestaurantResponse(BaseModel):
    id: int
    name: str
    location: str
    phone: Optional[str] = None
    owner_id: int
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# CATEGORY
# ============================================================

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class CategoryResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# FOOD ITEM
# ============================================================

class FoodItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., ge=0)
    category: str = Field(..., min_length=2, max_length=100)
    restaurant_id: int = Field(..., gt=0)


class FoodItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    category_id: Optional[int] = Field(None, gt=0)
    is_available: Optional[bool] = None


class FoodItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    category_id: Optional[int] = None
    restaurant_id: int
    is_available: bool = True

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# CART
# ============================================================

class CartItemCreate(BaseModel):
    food_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    id: int
    food_item_id: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: Optional[int] = None
    items: list[CartItemResponse]

    model_config = ConfigDict(from_attributes=True)


class CartTotalResponse(BaseModel):
    total: float


# ============================================================
# DELIVERY ADDRESS
# ============================================================

class AddressCreate(BaseModel):
    recipient_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=7, max_length=20)
    address_line: str = Field(..., min_length=3, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=4, max_length=20)
    is_default: bool = False


class AddressUpdate(BaseModel):
    recipient_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    address_line: Optional[str] = Field(None, min_length=3, max_length=300)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=4, max_length=20)
    is_default: Optional[bool] = None


class AddressResponse(BaseModel):
    id: int
    user_id: int
    recipient_name: str
    phone: str
    address_line: str
    city: str
    state: str
    postal_code: str
    is_default: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ORDER
# ============================================================

class OrderCreate(BaseModel):
    address_id: int = Field(..., gt=0)


class OrderStatusUpdate(BaseModel):
    status: Literal[
        "PENDING",
        "CONFIRMED",
        "PREPARING",
        "READY",
        "DELIVERED",
        "CANCELLED",
    ]

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value


class OrderItemResponse(BaseModel):
    id: int
    food_item_id: int
    quantity: int
    price: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    address_id: Optional[int] = None
    total_amount: float
    status: str
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)