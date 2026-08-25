"""Aggregate all versioned business routers in one place."""

from fastapi import APIRouter

from .admin import router as admin_router
from .ai import router as ai_router
from .auth import router as auth_router
from .chart_analysis import router as chart_analysis_router
from .chart_profiles import router as chart_profiles_router
from .compatibility import router as compatibility_router
from .fortunes import router as fortunes_router
from .guidance import router as guidance_router
from .payments import router as payments_router
from .reports import router as reports_router
from .users import router as users_router
from .ziwei import router as ziwei_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(admin_router)
router.include_router(payments_router)
router.include_router(chart_profiles_router)
router.include_router(fortunes_router)
router.include_router(guidance_router)
router.include_router(chart_analysis_router)
router.include_router(reports_router)
router.include_router(compatibility_router)
router.include_router(ziwei_router)
router.include_router(ai_router)
