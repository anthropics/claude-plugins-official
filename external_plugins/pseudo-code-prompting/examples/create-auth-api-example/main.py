from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from datetime import datetime

from config import settings
from database import init_db, init_default_roles
from rate_limiter import limiter
from routes import auth, password, token, email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Production Authentication API",
    description="A production-ready authentication API with JWT, token refresh, password reset, email verification, and account lockout",
    version=settings.API_VERSION
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"detail": "Rate limit exceeded"}
))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    ip_address = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path

    logger.info(f"Incoming request - IP: {ip_address} | Method: {method} | Path: {path}")

    response = await call_next(request)

    logger.info(f"Response - Method: {method} | Path: {path} | Status: {response.status_code}")
    return response

# Include routers
app.include_router(auth.router)
app.include_router(password.router)
app.include_router(token.router)
app.include_router(email.router)

@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "api_version": settings.API_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    logger.info("Starting application...")
    try:
        init_db()
        logger.info("Database initialized")
        init_default_roles()
        logger.info("Default roles initialized")
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
