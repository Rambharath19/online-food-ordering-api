from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import FoodItem, Restaurant, User, Category
from schemas import FoodItemCreate, FoodItemResponse, FoodItemUpdate
from dependencies import get_current_user


router = APIRouter(
    prefix="/foods",
    tags=["Food Items"]
)


# ============================================================
# HELPER: CHECK FOOD MANAGEMENT PERMISSION
# ============================================================

def check_food_permission(food, current_user, db):
    if current_user.role == "ADMIN":
        return

    if current_user.role != "RESTAURANT_OWNER":
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == food.restaurant_id
    ).first()

    if not restaurant or restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can manage food only for your own restaurant"
        )


# ============================================================
# CREATE FOOD ITEM
# ADMIN OR RESTAURANT OWNER
# ============================================================

@router.post(
    "/",
    response_model=FoodItemResponse,
    status_code=status.HTTP_201_CREATED
)
def create_food(
    food_data: FoodItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == food_data.restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if not restaurant.is_active:
        raise HTTPException(status_code=400, detail="Restaurant is inactive")

    if current_user.role == "RESTAURANT_OWNER":
        if restaurant.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can manage food only for your own restaurant"
            )
    elif current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")

    food_values = food_data.model_dump()

    # Link to the Category table when a matching category exists.
    category = db.query(Category).filter(
        Category.name.ilike(food_data.category.strip())
    ).first()

    food = FoodItem(
        name=food_data.name.strip(),
        description=food_data.description,
        price=food_data.price,
        category=food_data.category.strip(),
        category_id=category.id if category else None,
        restaurant_id=food_data.restaurant_id,
        is_available=True
    )

    db.add(food)
    db.commit()
    db.refresh(food)

    return food


# ============================================================
# GET FOOD ITEMS
# Search by name and filter by category/restaurant
# ============================================================

@router.get("/", response_model=list[FoodItemResponse])
def get_foods(
    search: Optional[str] = Query(None, min_length=1),
    category_id: Optional[int] = Query(None, gt=0),
    category: Optional[str] = Query(None, min_length=1),
    restaurant_id: Optional[int] = Query(None, gt=0),
    available_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(FoodItem).join(
        Restaurant,
        FoodItem.restaurant_id == Restaurant.id
    )

    # Customers see only available food from active restaurants.
    if current_user.role == "CUSTOMER":
        query = query.filter(
            FoodItem.is_available.is_(True),
            Restaurant.is_active.is_(True)
        )
    elif available_only:
        query = query.filter(
            FoodItem.is_available.is_(True),
            Restaurant.is_active.is_(True)
        )

    if search:
        query = query.filter(FoodItem.name.ilike(f"%{search.strip()}%"))

    if category_id is not None:
        query = query.filter(FoodItem.category_id == category_id)

    if category:
        query = query.filter(
            FoodItem.category.ilike(category.strip())
        )

    if restaurant_id is not None:
        query = query.filter(FoodItem.restaurant_id == restaurant_id)

    return query.order_by(FoodItem.name).all()


# ============================================================
# GET FOOD ITEM BY ID
# ============================================================

@router.get("/{food_id}", response_model=FoodItemResponse)
def get_food(
    food_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    food = db.query(FoodItem).join(
        Restaurant,
        FoodItem.restaurant_id == Restaurant.id
    ).filter(FoodItem.id == food_id).first()

    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")

    if current_user.role == "CUSTOMER":
        if not food.is_available or not food.restaurant.is_active:
            raise HTTPException(status_code=404, detail="Food item not available")

    return food


# ============================================================
# GET FOOD BY RESTAURANT
# ============================================================

@router.get(
    "/restaurant/{restaurant_id}",
    response_model=list[FoodItemResponse]
)
def get_foods_by_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    query = db.query(FoodItem).filter(
        FoodItem.restaurant_id == restaurant_id
    )

    if current_user.role == "CUSTOMER":
        if not restaurant.is_active:
            raise HTTPException(status_code=404, detail="Restaurant not available")

        query = query.filter(FoodItem.is_available.is_(True))

    return query.order_by(FoodItem.name).all()


# ============================================================
# UPDATE FOOD ITEM
# ADMIN OR OWN RESTAURANT OWNER
# ============================================================

@router.put("/{food_id}", response_model=FoodItemResponse)
def update_food(
    food_id: int,
    food_data: FoodItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    food = db.query(FoodItem).filter(
        FoodItem.id == food_id
    ).first()

    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")

    check_food_permission(food, current_user, db)

    changes = food_data.model_dump(exclude_unset=True)

    # Do not allow an owner to move food to another restaurant.
    if "restaurant_id" in changes:
        raise HTTPException(
            status_code=400,
            detail="Changing a food item's restaurant is not supported"
        )

    if "category_id" in changes and changes["category_id"] is not None:
        category_exists = db.query(Category).filter(
            Category.id == changes["category_id"]
        ).first()

        if not category_exists:
            raise HTTPException(status_code=404, detail="Category not found")

        food.category = category_exists.name

    if "category" in changes and changes["category"] is not None:
        category_record = db.query(Category).filter(
            Category.name.ilike(changes["category"].strip())
        ).first()

        if not category_record:
            raise HTTPException(
                status_code=404,
                detail="Category not found. Create the category first."
            )

        food.category = category_record.name
        food.category_id = category_record.id

    for field, value in changes.items():
        if field not in {"category", "category_id"}:
            setattr(food, field, value)

    db.commit()
    db.refresh(food)

    return food


# ============================================================
# DELETE FOOD ITEM
# ADMIN OR OWN RESTAURANT OWNER
# ============================================================

@router.delete("/{food_id}")
def delete_food(
    food_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    food = db.query(FoodItem).filter(
        FoodItem.id == food_id
    ).first()

    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")

    check_food_permission(food, current_user, db)

    # Preserve historical order items and cart references.
    # Deactivate the food instead of permanently deleting it.
    food.is_available = False

    db.commit()

    return {"message": "Food item deactivated successfully"}