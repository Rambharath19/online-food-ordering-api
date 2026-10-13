from fastapi import FastAPI
from database import engine, Base, SessionLocal
import models

from routers.auth import router as auth_router
from routers.restaurants import router as restaurant_router

from auth import hash_password
from routers.foods import router as food_router
from routers.cart import router as cart_router
from routers.orders import router as order_router
from routers import categories
from routers import addresses


# ============================================================
# CREATE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# CREATE DEFAULT ADMIN
# ============================================================

def create_default_admin():

    db = SessionLocal()

    try:

        admin_email = "admin@gmail.com"

        existing_admin = db.query(models.User).filter(
            models.User.email == admin_email
        ).first()

        if not existing_admin:

            admin = models.User(
                name="Administrator",
                email=admin_email,
                password=hash_password("Admin@123"),
                role="ADMIN"
            )

            db.add(admin)
            db.commit()

    finally:
        db.close()


create_default_admin()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Online Food Ordering API",
    description="Online Food Ordering System using FastAPI and MySQL",
    version="1.0.0"
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(restaurant_router)
app.include_router(food_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(categories.router)
app.include_router(addresses.router)

# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Online Food Ordering API is running"
    }