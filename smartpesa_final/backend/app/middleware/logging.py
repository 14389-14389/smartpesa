import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request
        logger.info(
            f"{datetime.utcnow().isoformat()} - "
            f"{client_host} - {method} {url} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s"
        )
        
        return response

class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log sensitive operations for audit trail"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Log sensitive operations (POST, PUT, DELETE)
        if request.method in ["POST", "PUT", "DELETE"]:
            user = request.headers.get("Authorization", "unknown")[:20] + "..."
            logger.info(
                f"AUDIT: {request.method} {request.url.path} - "
                f"User: {user} - Status: {response.status_code}"
            )
        
        return response
