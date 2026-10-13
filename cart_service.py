from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Cart, CartItem, FoodItem, Restaurant


# ============================================================
# GET OR CREATE CART
# ============================================================

def get_or_create_cart(db: Session, user_id: int):
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    if not cart:
        cart = Cart(
            user_id=user_id,
            restaurant_id=None,
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)

    return cart


# ============================================================
# ADD FOOD TO CART
# ============================================================

def add_to_cart(
    db: Session,
    user_id: int,
    food_item_id: int,
    quantity: int,
):
    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0",
        )

    try:
        food = db.query(FoodItem).filter(
            FoodItem.id == food_item_id
        ).first()

        if not food:
            raise HTTPException(
                status_code=404,
                detail="Food item not found",
            )

        if not food.is_available:
            raise HTTPException(
                status_code=400,
                detail="Food item is currently unavailable",
            )

        restaurant = db.query(Restaurant).filter(
            Restaurant.id == food.restaurant_id
        ).first()

        if not restaurant:
            raise HTTPException(
                status_code=404,
                detail="Restaurant not found",
            )

        if not restaurant.is_active:
            raise HTTPException(
                status_code=400,
                detail="Restaurant is currently unavailable",
            )

        cart = get_or_create_cart(db, user_id)

        if cart.restaurant_id is None:
            cart.restaurant_id = food.restaurant_id

        elif cart.restaurant_id != food.restaurant_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Your cart contains food from another restaurant. "
                    "Clear your cart before adding food from a different restaurant."
                ),
            )

        cart_item = db.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.food_item_id == food_item_id,
        ).first()

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                food_item_id=food_item_id,
                quantity=quantity,
            )
            db.add(cart_item)

        db.commit()
        db.refresh(cart_item)

        return cart_item

    except Exception:
        db.rollback()
        raise


# ============================================================
# UPDATE CART ITEM QUANTITY
# ============================================================

def update_cart_item(
    db: Session,
    user_id: int,
    cart_item_id: int,
    quantity: int,
):
    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0",
        )

    try:
        cart = get_or_create_cart(db, user_id)

        cart_item = db.query(CartItem).filter(
            CartItem.id == cart_item_id,
            CartItem.cart_id == cart.id,
        ).first()

        if not cart_item:
            raise HTTPException(
                status_code=404,
                detail="Cart item not found",
            )

        food = cart_item.food_item

        if not food or not food.is_available:
            raise HTTPException(
                status_code=400,
                detail="Food item is currently unavailable",
            )

        restaurant = db.query(Restaurant).filter(
            Restaurant.id == food.restaurant_id
        ).first()

        if not restaurant or not restaurant.is_active:
            raise HTTPException(
                status_code=400,
                detail="Restaurant is currently unavailable",
            )

        cart_item.quantity = quantity

        db.commit()
        db.refresh(cart_item)

        return cart_item

    except Exception:
        db.rollback()
        raise


# ============================================================
# REMOVE FOOD FROM CART
# ============================================================

def remove_from_cart(
    db: Session,
    user_id: int,
    cart_item_id: int,
):
    try:
        cart = get_or_create_cart(db, user_id)

        cart_item = db.query(CartItem).filter(
            CartItem.id == cart_item_id,
            CartItem.cart_id == cart.id,
        ).first()

        if not cart_item:
            raise HTTPException(
                status_code=404,
                detail="Cart item not found",
            )

        db.delete(cart_item)
        db.flush()

        remaining_items = db.query(CartItem).filter(
            CartItem.cart_id == cart.id
        ).count()

        if remaining_items == 0:
            cart.restaurant_id = None

        db.commit()

        return {
            "message": "Food removed from cart successfully",
        }

    except Exception:
        db.rollback()
        raise


# ============================================================
# CLEAR CART
# ============================================================

def clear_cart(db: Session, user_id: int):
    try:
        cart = get_or_create_cart(db, user_id)

        db.query(CartItem).filter(
            CartItem.cart_id == cart.id
        ).delete(synchronize_session=False)

        cart.restaurant_id = None

        db.commit()

        return {
            "message": "Cart cleared successfully",
        }

    except Exception:
        db.rollback()
        raise


# ============================================================
# CALCULATE CART TOTAL
# ============================================================

def calculate_cart_total(cart):
    total = 0.0

    for item in cart.items:
        if item.food_item:
            total += item.food_item.price * item.quantity

    return round(total, 2)