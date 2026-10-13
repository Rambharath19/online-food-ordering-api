from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


# Create category (Admin only)
@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create categories",
        )

    existing = db.query(models.Category).filter(
        models.Category.name.ilike(category.name.strip())
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category already exists",
        )

    new_category = models.Category(name=category.name.strip())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


# Get all categories
@router.get("/", response_model=list[schemas.CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(models.Category).order_by(models.Category.name).all()


# Get category by ID
@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


# Update category (Admin only)
@router.put("/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    category_data: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin can update categories")

    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    duplicate = db.query(models.Category).filter(
        models.Category.name.ilike(category_data.name.strip()),
        models.Category.id != category_id,
    ).first()

    if duplicate:
        raise HTTPException(status_code=409, detail="Category already exists")

    category.name = category_data.name.strip()
    db.commit()
    db.refresh(category)

    return category


# Delete category (Admin only)
@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin can delete categories")

    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if db.query(models.FoodItem).filter(
        models.FoodItem.category_id == category_id
    ).first():
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a category assigned to food items",
        )

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}