from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.routes import users, businesses, transactions, forecast, inventory, suppliers, credit

# Import middleware
from app.middleware.logging import RequestLoggingMiddleware, AuditLogMiddleware
from app.middleware.security import SecurityHeadersMiddleware

app = FastAPI(
    title="SmartPesa API",
    description="Intelligent Cash Flow Forecasting for SMEs",
    version="2.0.0"
)

# Get CORS origins from environment
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(AuditLogMiddleware)

# Include routers
app.include_router(users.router)
app.include_router(businesses.router)
app.include_router(transactions.router)
app.include_router(forecast.router)
app.include_router(inventory.router)
app.include_router(suppliers.router)
app.include_router(credit.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to SmartPesa API",
        "version": "2.0",
        "phase": "Production Ready",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "users": {
                "register": "POST /users/register",
                "login": "POST /users/login",
                "me": "GET /users/me"
            },
            "businesses": {
                "create": "POST /businesses/",
                "list": "GET /businesses/",
                "get": "GET /businesses/{id}",
                "update": "PUT /businesses/{id}",
                "delete": "DELETE /businesses/{id}"
            },
            "transactions": {
                "create": "POST /transactions/",
                "list": "GET /transactions/",
                "get": "GET /transactions/{id}",
                "update": "PUT /transactions/{id}",
                "delete": "DELETE /transactions/{id}",
                "summary": "GET /transactions/summary/overview",
                "by_category": "GET /transactions/analysis/by-category",
                "daily_totals": "GET /transactions/analysis/daily-totals"
            },
            "forecast": {
                "7day": "GET /forecast/{business_id}/7days",
                "30day": "GET /forecast/{business_id}/30days",
                "risk_alert": "GET /forecast/{business_id}/risk-alert",
                "health": "GET /forecast/{business_id}/health"
            },
            "inventory": {
                "create": "POST /inventory/",
                "list": "GET /inventory/?business_id={id}",
                "get": "GET /inventory/{id}",
                "update": "PUT /inventory/{id}",
                "delete": "DELETE /inventory/{id}",
                "add_stock": "POST /inventory/{id}/add-stock?quantity={q}",
                "remove_stock": "POST /inventory/{id}/remove-stock?quantity={q}",
                "low_stock_alerts": "GET /inventory/alerts/low-stock?business_id={id}"
            },
            "suppliers": {
                "create": "POST /suppliers/",
                "list": "GET /suppliers/?business_id={id}",
                "get": "GET /suppliers/{id}",
                "update": "PUT /suppliers/{id}",
                "delete": "DELETE /suppliers/{id}",
                "create_payment": "POST /suppliers/payments",
                "list_payments": "GET /suppliers/payments/all?business_id={id}",
                "mark_paid": "PUT /suppliers/payments/{id}/pay",
                "outstanding_summary": "GET /suppliers/outstanding/summary?business_id={id}",
                "outstanding_by_supplier": "GET /suppliers/outstanding/by-supplier?business_id={id}"
            },
            "credit": {
                "get_score": "GET /credit/business/{business_id}",
                "score_history": "GET /credit/business/{business_id}/history",
                "lender_profile": "GET /credit/lender/business/{business_id}",
                "lender_businesses": "GET /credit/lender/businesses",
                "calculate_all": "POST /credit/calculate-all"
            }
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
