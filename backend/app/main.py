"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v2.api import api_router_v2


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - MUST be added BEFORE other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Security headers middleware (relaxed for localhost development)
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Changed from DENY to SAMEORIGIN
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Removed strict HSTS for localhost development
    if not request.url.hostname in ["localhost", "127.0.0.1"]:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Relaxed CSP for localhost development
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* ws://localhost:*"
    return response

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router_v2, prefix="/api/v2")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Draizer AI Trading Platform API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": "backend"
    }



