from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from fastapi.responses import JSONResponse

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

def add_rate_limiting(app):
    """Add rate limiting to the application"""
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    print("✅ Rate limiting enabled")
    
    return limiter

# Custom rate limit exceeded handler
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
        }
    )
