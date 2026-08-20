"""Aggregate all versioned business routers in one place."""

from fastapi import APIRouter

from .admin import router as admin_router
from .auth import router as auth_router
from .chart_profiles import router as chart_profiles_router
from .payments import router as payments_router
from .users import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(admin_router)
router.include_router(payments_router)
router.include_router(chart_profiles_router)
