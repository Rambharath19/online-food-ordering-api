from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Restaurant, User
from schemas import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
)
from dependencies import get_current_user


router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"],
)


# ============================================================
# ADMIN CHECK
# ============================================================

def require_admin(current_user: User):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )


# ============================================================
# CREATE RESTAURANT
# ADMIN ONLY
# ============================================================

@router.post(
    "/",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    owner = db.query(User).filter(
        User.id == restaurant_data.owner_id
    ).first()

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Restaurant owner not found",
        )

    if owner.role != "RESTAURANT_OWNER":
        raise HTTPException(
            status_code=400,
            detail="Selected user is not a restaurant owner",
        )

    existing = db.query(Restaurant).filter(
        Restaurant.owner_id == owner.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This owner already has a restaurant",
        )

    restaurant = Restaurant(
        name=restaurant_data.name.strip(),
        location=restaurant_data.location.strip(),
        phone=restaurant_data.phone,
        owner_id=owner.id,
        is_active=True,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


# ============================================================
# GET RESTAURANTS
# SEARCH BY NAME / FILTER BY ACTIVE STATUS
# ============================================================

@router.get(
    "/",
    response_model=list[RestaurantResponse],
)
def get_restaurants(
    search: Optional[str] = Query(None, min_length=1),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Restaurant)

    # Customers must only see active restaurants.
    if current_user.role == "CUSTOMER":
        query = query.filter(Restaurant.is_active.is_(True))
    elif active_only:
        query = query.filter(Restaurant.is_active.is_(True))

    if search:
        query = query.filter(
            Restaurant.name.ilike(f"%{search.strip()}%")
        )

    return query.order_by(Restaurant.name).all()


# ============================================================
# GET RESTAURANT BY ID
# ============================================================

@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    if current_user.role == "CUSTOMER" and not restaurant.is_active:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not available",
        )

    return restaurant


# ============================================================
# UPDATE RESTAURANT
# ADMIN OR OWNER OF THAT RESTAURANT
# ============================================================

@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
)
def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    if current_user.role == "RESTAURANT_OWNER":
        if restaurant.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can manage only your own restaurant",
            )
    elif current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    changes = restaurant_data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)

    return restaurant


# ============================================================
# ACTIVATE / DEACTIVATE RESTAURANT
# ADMIN ONLY
# ============================================================

@router.patch(
    "/{restaurant_id}/availability",
    response_model=RestaurantResponse,
)
def change_restaurant_availability(
    restaurant_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    restaurant.is_active = is_active

    db.commit()
    db.refresh(restaurant)

    return restaurant


# ============================================================
# DELETE RESTAURANT
# ADMIN ONLY — SOFT DELETE
# ============================================================

@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    # Keep order history and food records intact.
    restaurant.is_active = False

    db.commit()

    return {
        "message": "Restaurant deactivated successfully",
    }