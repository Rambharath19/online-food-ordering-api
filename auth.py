from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Cart
from schemas import (
    UserCreate,
    UserResponse,
    OwnerCreate,
    OwnerResponse,
    LoginRequest,
    TokenResponse
)
from auth import (
    hash_password,
    verify_password,
    create_access_token
)
from dependencies import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# CUSTOMER REGISTRATION
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Check existing email
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Always create CUSTOMER
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(user_data.password),
        role="CUSTOMER"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create cart automatically
    cart = Cart(user_id=user.id)

    db.add(cart)
    db.commit()

    return user


# ============================================================
# CREATE RESTAURANT OWNER
# ADMIN ONLY
# ============================================================

@router.post(
    "/register-owner",
    response_model=OwnerResponse
)
def register_owner(
    owner_data: OwnerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Only ADMIN can create owners
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    # Check existing email
    existing_user = db.query(User).filter(
        User.email == owner_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create RESTAURANT_OWNER
    owner = User(
        name=owner_data.name,
        email=owner_data.email,
        password=hash_password(owner_data.password),
        role="RESTAURANT_OWNER"
    )

    db.add(owner)
    db.commit()
    db.refresh(owner)

    return owner


# ============================================================
# LOGIN
# ADMIN / CUSTOMER / RESTAURANT_OWNER
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == login_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        login_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }