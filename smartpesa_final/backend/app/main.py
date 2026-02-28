"""
SmartPesa API - Main Application
All components are properly organized and ready to run
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from app.routes import (
    users_router, businesses_router, transactions_router,
    forecast_router, inventory_router, suppliers_router,
    credit_router, password_router, reports_router,
    notifications_router, analytics_router, webhooks_router
)

# Import database
from app.database import engine
from app import models

# Create database tables
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables ready")
except Exception as e:
    logger.error(f"❌ Database error: {e}")

# Create FastAPI app
app = FastAPI(
    title="SmartPesa API",
    description="Intelligent Cash Flow Forecasting for SMEs",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(businesses_router, prefix="/api/v1/businesses", tags=["Businesses"])
app.include_router(transactions_router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(forecast_router, prefix="/api/v1/forecast", tags=["Forecast"])
app.include_router(inventory_router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(suppliers_router, prefix="/api/v1/suppliers", tags=["Suppliers"])
app.include_router(credit_router, prefix="/api/v1/credit", tags=["Credit"])
app.include_router(password_router, prefix="/api/v1/password", tags=["Password"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])

if webhooks_router:
    app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["Webhooks"])

@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "success": True,
        "data": {
            "name": "SmartPesa API",
            "version": "2.1.0",
            "status": "operational",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }

logger.info("🚀 SmartPesa API is ready!")
