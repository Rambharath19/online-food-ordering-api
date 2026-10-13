from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Restaurant,
    Address,
    FoodItem,
)


# ============================================================
# PLACE ORDER
# ============================================================

def create_order(
    db: Session,
    user_id: int,
    address_id: int,
):
    try:
        # Get customer cart
        cart = db.query(Cart).filter(
            Cart.user_id == user_id
        ).first()

        if not cart:
            raise HTTPException(
                status_code=404,
                detail="Cart not found",
            )

        # Check cart items
        if not cart.items:
            raise HTTPException(
                status_code=400,
                detail="Cart is empty",
            )

        # Check restaurant selection
        if cart.restaurant_id is None:
            raise HTTPException(
                status_code=400,
                detail="Restaurant not selected",
            )

        # Validate delivery address belongs to customer
        address = db.query(Address).filter(
            Address.id == address_id,
            Address.user_id == user_id,
        ).first()

        if not address:
            raise HTTPException(
                status_code=404,
                detail="Delivery address not found",
            )

        # Check restaurant
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == cart.restaurant_id
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

        # Validate food and calculate total
        total_amount = 0.0
        validated_items = []

        for cart_item in cart.items:
            food = db.query(FoodItem).filter(
                FoodItem.id == cart_item.food_item_id
            ).first()

            if not food:
                raise HTTPException(
                    status_code=404,
                    detail=f"Food item {cart_item.food_item_id} not found",
                )

            if food.restaurant_id != restaurant.id:
                raise HTTPException(
                    status_code=400,
                    detail="All cart items must belong to the selected restaurant",
                )

            if not food.is_available:
                raise HTTPException(
                    status_code=400,
                    detail=f"{food.name} is currently unavailable",
                )

            if cart_item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Quantity must be greater than zero",
                )

            total_amount += food.price * cart_item.quantity

            validated_items.append({
                "food_id": food.id,
                "quantity": cart_item.quantity,
                "price": food.price,
            })

        total_amount = round(total_amount, 2)

        # Create order
        order = Order(
            user_id=user_id,
            restaurant_id=restaurant.id,
            address_id=address.id,
            total_amount=total_amount,
            status="PENDING",
        )

        db.add(order)
        db.flush()

        # Save order items
        for item in validated_items:
            order_item = OrderItem(
                order_id=order.id,
                food_item_id=item["food_id"],
                quantity=item["quantity"],
                price=item["price"],
            )
            db.add(order_item)

        # Clear cart after creating order
        db.query(CartItem).filter(
            CartItem.cart_id == cart.id
        ).delete(synchronize_session=False)

        cart.restaurant_id = None

        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise


# ============================================================
# GET CUSTOMER ORDERS
# ============================================================

def get_customer_orders(
    db: Session,
    user_id: int,
):
    return db.query(Order).filter(
        Order.user_id == user_id
    ).order_by(
        Order.created_at.desc()
    ).all()


# ============================================================
# GET ORDER BY ID
# ============================================================

def get_order(
    db: Session,
    order_id: int,
):
    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


# ============================================================
# GET RESTAURANT ORDERS
# ============================================================

def get_restaurant_orders(
    db: Session,
    restaurant_id: int,
):
    return db.query(Order).filter(
        Order.restaurant_id == restaurant_id
    ).order_by(
        Order.created_at.desc()
    ).all()


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

def update_order_status(
    db: Session,
    order_id: int,
    status: str,
):
    order = get_order(db, order_id)

    status = status.strip().upper()
    current_status = order.status.upper()

    # Support orders created by the previous version
    if current_status == "PLACED":
        current_status = "PENDING"

    allowed_transitions = {
        "PENDING": ["CONFIRMED", "CANCELLED"],
        "CONFIRMED": ["PREPARING", "CANCELLED"],
        "PREPARING": ["READY"],
        "READY": ["DELIVERED"],
        "DELIVERED": [],
        "CANCELLED": [],
    }

    if status not in allowed_transitions:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status",
        )

    if status not in allowed_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change order status from "
                f"{current_status} to {status}"
            ),
        )

    try:
        order.status = status
        db.commit()
        db.refresh(order)
        return order

    except Exception:
        db.rollback()
        raise