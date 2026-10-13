# Online Food Ordering API

## Overview
A REST API built using FastAPI, Python, MySQL, SQLAlchemy, Pydantic, and JWT authentication. It supports user authentication, restaurant and food management, categories, shopping carts, delivery addresses, and order processing.

## Requirements
- Python 3.10 or compatible version
- MySQL Server and MySQL Workbench
- pip

## Setup
1. Create the MySQL database named `online_food_ordering_db`.
2. Configure the database connection and JWT settings in `.env`.
3. Create and activate a Python virtual environment.
4. Install dependencies using `pip install -r requirements.txt`.

## Run the application
Run the following command from the project root:

`uvicorn main:app --reload --port 8001`

## API documentation
Open `http://127.0.0.1:8001/docs` in a browser.

## Main features
- User registration and login with JWT authentication
- Role-based authorization
- Restaurant and food management
- Food category management and search
- Shopping cart operations and total calculation
- Delivery address management
- Order placement, history, cancellation, and status management


#structure

D:\online_food_ordering\
├── main.py
├── database.py
├── models.py
├── schemas.py
├── auth.py
├── dependencies.py
├── routers\
├── services\
├── requirements.txt
├── .env.example
├── README.md
└── screenshots\
