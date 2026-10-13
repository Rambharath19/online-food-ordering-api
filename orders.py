from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Order, Address
from schemas import OrderResponse, OrderCreate, OrderStatusUpdate
from dependencies import get_current_user

from services.order_service import (
    create_order,
    get_customer_orders,
    get_order,
    get_restaurant_orders,
    update_order_status,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


# ============================================================
# CUSTOMER CHECK
# ============================================================

def require_customer(current_user: User):
    if current_user.role != "CUSTOMER":
        raise HTTPException(
            status_code=403,
            detail="Only customers can perform this action",
        )


# ============================================================
# PLACE ORDER
# ============================================================

@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def place_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)

    address = db.query(Address).filter(
        Address.id == order_data.address_id,
        Address.user_id == current_user.id,
    ).first()

    if not address:
        raise HTTPException(
            status_code=404,
            detail="Delivery address not found for this customer",
        )

    return create_order(
        db=db,
        user_id=current_user.id,
        address_id=order_data.address_id,
    )


# ============================================================
# CUSTOMER'S ORDERS
# ============================================================

@router.get(
    "/my-orders",
    response_model=list[OrderResponse],
)
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)

    return get_customer_orders(
        db=db,
        user_id=current_user.id,
    )


# ============================================================
# RESTAURANT OWNER'S ORDERS
# ============================================================

@router.get(
    "/restaurant/my-orders",
    response_model=list[OrderResponse],
)
def restaurant_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "RESTAURANT_OWNER":
        raise HTTPException(
            status_code=403,
            detail="Only restaurant owners can access this endpoint",
        )

    if not current_user.restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not assigned",
        )

    return get_restaurant_orders(
        db=db,
        restaurant_id=current_user.restaurant.id,
    )


# ============================================================
# GET ORDER DETAILS
# CUSTOMER / ADMIN / RESTAURANT OWNER
# ============================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order(db=db, order_id=order_id)

    if current_user.role == "ADMIN":
        return order

    if current_user.role == "CUSTOMER":
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can view only your own orders",
            )
        return order

    if current_user.role == "RESTAURANT_OWNER":
        if order.restaurant.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can view only your restaurant orders",
            )
        return order

    raise HTTPException(status_code=403, detail="Access denied")


# ============================================================
# UPDATE ORDER STATUS
# ADMIN / RESTAURANT OWNER
# ============================================================

@router.put(
    "/{order_id}/status",
    response_model=OrderResponse,
)
def change_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order(db=db, order_id=order_id)

    if current_user.role == "RESTAURANT_OWNER":
        if order.restaurant.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can manage only your restaurant orders",
            )
    elif current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only admins and restaurant owners can update order status",
        )

    current_status = order.status.upper()
    new_status = status_data.status.upper()

    allowed_transitions = {
        "PENDING": ["CONFIRMED", "CANCELLED"],
        "CONFIRMED": ["PREPARING", "CANCELLED"],
        "PREPARING": ["READY"],
        "READY": ["DELIVERED"],
        "DELIVERED": [],
        "CANCELLED": [],
    }

    if new_status not in allowed_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change order status from {current_status} to {new_status}",
        )

    return update_order_status(
        db=db,
        order_id=order_id,
        status=new_status,
    )


# ============================================================
# CANCEL CUSTOMER'S OWN ORDER
# ============================================================

@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_customer(current_user)

    order = get_order(db=db, order_id=order_id)

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can cancel only your own orders",
        )

    if order.status.upper() not in ["PENDING", "CONFIRMED"]:
        raise HTTPException(
            status_code=400,
            detail="Only pending or confirmed orders can be cancelled",
        )

    return update_order_status(
        db=db,
        order_id=order_id,
        status="CANCELLED",
    )