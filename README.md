# TE Project py

A FastAPI backend for managing employee data collection with role-based access control, file uploads, and report generation.

## Features

- JWT Authentication with role-based access control
- File upload system with validation
- Excel report generation
- Admin management
- Rate limiting
- Structured logging

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and update the values
5. Run database migrations:
   ```
   alembic upgrade head
   ```
6. Start the server:
   ```
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
data_collection_system/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── submissions.py
│   │   └── admin.py
│   ├── schemas.py
│   ├── database.py
│   ├── security.py
│   ├── storage.py
│   ├── dependencies.py
│   ├── reports.py
│   └── config.py
├── migrations/
│   └── versions/
├── uploads/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Testing

Run tests with:
```
pytest
```