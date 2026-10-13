from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import CartItemCreate, CartResponse
from dependencies import get_current_user

from services.cart_service import (
    get_or_create_cart,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    calculate_cart_total
)


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


# ============================================================
# CUSTOMER CHECK
# ============================================================

def require_customer(current_user: User):

    if current_user.role != "CUSTOMER":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Only customers can access the cart"
        )


# ============================================================
# GET MY CART
# ============================================================

@router.get(
    "/",
    response_model=CartResponse
)
def get_my_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_customer(current_user)

    cart = get_or_create_cart(
        db,
        current_user.id
    )

    return cart


# ============================================================
# ADD FOOD TO CART
# ============================================================

@router.post(
    "/items"
)
def add_food_to_cart(
    cart_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_customer(current_user)

    cart_item = add_to_cart(
        db=db,
        user_id=current_user.id,
        food_item_id=cart_data.food_item_id,
        quantity=cart_data.quantity
    )

    return {
        "message": "Food added to cart successfully",
        "cart_item_id": cart_item.id,
        "food_item_id": cart_item.food_item_id,
        "quantity": cart_item.quantity
    }


# ============================================================
# UPDATE CART ITEM
# ============================================================

@router.put(
    "/items/{cart_item_id}"
)
def update_cart(
    cart_item_id: int,
    cart_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_customer(current_user)

    cart_item = update_cart_item(
        db=db,
        user_id=current_user.id,
        cart_item_id=cart_item_id,
        quantity=cart_data.quantity
    )

    return {
        "message": "Cart updated successfully",
        "cart_item_id": cart_item.id,
        "food_item_id": cart_item.food_item_id,
        "quantity": cart_item.quantity
    }


# ============================================================
# REMOVE FOOD FROM CART
# ============================================================

@router.delete(
    "/items/{cart_item_id}"
)
def remove_food_from_cart(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_customer(current_user)

    return remove_from_cart(
        db=db,
        user_id=current_user.id,
        cart_item_id=cart_item_id
    )


# ============================================================
# CLEAR CART
# ============================================================

@router.delete(
    "/"
)
def clear_my_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_customer(current_user)

    return clear_cart(
        db=db,
        user_id=current_user.id
    )


# ============================================================
# GET CART TOTAL
# ============================================================

@router.get(
    "/total"
)
def get_cart_total(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_customer(current_user)

    cart = get_or_create_cart(
        db,
        current_user.id
    )

    total = calculate_cart_total(cart)

    return {
        "total_amount": total
    }