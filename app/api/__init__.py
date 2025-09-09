from .auth.routes import router as auth_router
from .superadmin.routes import router as superadmin_router

__all__ = ["auth_router", "superadmin_router"]



