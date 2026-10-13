from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/addresses", tags=["Addresses"])


# Add delivery address
@router.post("/", response_model=schemas.AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    address_data: schemas.AddressCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(
            status_code=403,
            detail="Only customers can manage delivery addresses",
        )

    if address_data.is_default:
        db.query(models.Address).filter(
            models.Address.user_id == current_user.id
        ).update({"is_default": False})

    address = models.Address(
        **address_data.model_dump(),
        user_id=current_user.id,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


# Get current customer's addresses
@router.get("/", response_model=list[schemas.AddressResponse])
def get_addresses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Only customers can view addresses")

    return db.query(models.Address).filter(
        models.Address.user_id == current_user.id
    ).order_by(models.Address.id.desc()).all()


# Get one address
@router.get("/{address_id}", response_model=schemas.AddressResponse)
def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Only customers can view addresses")

    address = db.query(models.Address).filter(
        models.Address.id == address_id,
        models.Address.user_id == current_user.id,
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    return address


# Update address
@router.put("/{address_id}", response_model=schemas.AddressResponse)
def update_address(
    address_id: int,
    address_data: schemas.AddressUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Only customers can update addresses")

    address = db.query(models.Address).filter(
        models.Address.id == address_id,
        models.Address.user_id == current_user.id,
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    changes = address_data.model_dump(exclude_unset=True)

    if changes.get("is_default") is True:
        db.query(models.Address).filter(
            models.Address.user_id == current_user.id,
            models.Address.id != address_id,
        ).update({"is_default": False})

    for field, value in changes.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)

    return address


# Delete address
@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Only customers can delete addresses")

    address = db.query(models.Address).filter(
        models.Address.id == address_id,
        models.Address.user_id == current_user.id,
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    if db.query(models.Order).filter(
        models.Order.address_id == address_id
    ).first():
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an address used by an order",
        )

    db.delete(address)
    db.commit()

    return {"message": "Address deleted successfully"}