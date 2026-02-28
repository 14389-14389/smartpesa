"""
Routes package - Export all routers
"""

from .users import router as users_router
from .businesses import router as businesses_router
from .transactions import router as transactions_router
from .forecast import router as forecast_router
from .inventory import router as inventory_router
from .suppliers import router as suppliers_router
from .credit import router as credit_router
from .password import router as password_router
from .reports import router as reports_router
from .notifications import router as notifications_router
from .analytics import router as analytics_router

# Try to import optional routers
try:
    from .webhooks import router as webhooks_router
except ImportError:
    webhooks_router = None

__all__ = [
    'users_router',
    'businesses_router',
    'transactions_router',
    'forecast_router',
    'inventory_router',
    'suppliers_router',
    'credit_router',
    'password_router',
    'reports_router',
    'notifications_router',
    'analytics_router',
    'webhooks_router'
]
