from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from loguru import logger
import os
import time

from .config import settings
from .routers import auth, submissions, admin
from .database import engine, Base

# Configure logger
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time} {level} {message}",
    backtrace=True,
    diagnose=True,
)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI backend for TE Project data collection system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Add rate limits to routes
@limiter.limit("5/minute")
@app.post("/auth/login")
async def limiter_login_proxy(request: Request):
    # This is just a proxy for rate limiting
    pass

@limiter.limit("3/minute")
@app.post("/auth/reset-password")
async def limiter_reset_password_proxy(request: Request):
    # This is just a proxy for rate limiting
    pass

@limiter.limit("10/minute")
@app.post("/submissions/")
async def limiter_create_submission_proxy(request: Request):
    # This is just a proxy for rate limiting
    pass

# Include routers
app.include_router(auth.router)
app.include_router(submissions.router)
app.include_router(admin.router)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Status code: {response.status_code}, Processed in: {process_time:.4f}s")
    return response

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

@app.get("/")
async def root():
    return {"message": "Welcome to TE Project API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}