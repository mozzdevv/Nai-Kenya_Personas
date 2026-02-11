"""
Security Module
Production-level security hardening for the API.
"""

from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import os
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)


# ============ Rate Limiting ============

class RateLimiter:
    """In-memory rate limiter with sliding window."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for this IP."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # Record this request
        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter(requests_per_minute=100)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        # Check rate limit
        if not rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content='{"detail": "Too many requests"}',
                status_code=429,
                media_type="application/json"
            )
        
        return await call_next(request)


# ============ Security Headers ============

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (only in production with HTTPS)
        if os.getenv("PRODUCTION", "false").lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# ============ Request Logging ============

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security auditing."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        # Process request
        response = await call_next(request)
        
        # Log request
        process_time = time.time() - start_time
        logger.info(
            f"{client_ip} - {request.method} {request.url.path} "
            f"- {response.status_code} - {process_time:.3f}s"
        )
        
        return response


# ============ Input Sanitization ============

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Basic HTML entity encoding for XSS prevention
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
    
    return text


# ============ Secure Token Generation ============

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str, salt: str = None) -> str:
    """Hash sensitive data for storage."""
    if salt is None:
        salt = os.getenv("HASH_SALT", "kikuyu-default-salt")
    
    return hashlib.sha256(f"{salt}{data}".encode()).hexdigest()


# ============ CORS Configuration ============

def get_cors_origins() -> list:
    """Get allowed CORS origins from environment."""
    origins_str = os.getenv("CORS_ORIGINS", "*")
    
    if origins_str == "*":
        # Development mode - allow all
        return ["*"]
    
    # Production - parse comma-separated origins
    return [origin.strip() for origin in origins_str.split(",")]


def configure_cors(app):
    """Configure CORS middleware with appropriate settings."""
    origins = get_cors_origins()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=86400,  # Cache preflight for 24 hours
    )


# ============ Environment Validation ============

def validate_production_config():
    """Validate that production config has proper secrets."""
    warnings = []
    
    # Check for default/weak secrets
    secret_key = os.getenv("DASHBOARD_SECRET_KEY", "")
    if not secret_key or "default" in secret_key.lower() or len(secret_key) < 32:
        warnings.append("DASHBOARD_SECRET_KEY should be a strong random string (32+ chars)")
    
    password = os.getenv("DASHBOARD_PASSWORD", "")
    if not password or password == "kikuyu2024" or len(password) < 12:
        warnings.append("DASHBOARD_PASSWORD should be changed from default (12+ chars)")
    
    # Check for required env vars
    required = ["GROK_API_KEY", "CLAUDE_API_KEY", "PINECONE_API_KEY"]
    for var in required:
        if not os.getenv(var):
            warnings.append(f"Missing required environment variable: {var}")
    
    if warnings:
        for warning in warnings:
            logger.warning(f"Security Warning: {warning}")
    
    return len(warnings) == 0


# ============ Apply All Security ============

def apply_security_middleware(app):
    """Apply all security middleware to the FastAPI app."""
    
    # Order matters - applied in reverse order when processing requests
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Configure CORS
    configure_cors(app)
    
    # Validate production config
    if os.getenv("PRODUCTION", "false").lower() == "true":
        validate_production_config()
    
    logger.info("Security middleware applied")
