from api.routes import users
from api.routes import health_profiles
from api.routes import analyze
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(users.router, prefix="/api")
api_router.include_router(health_profiles.router, prefix="/api")
api_router.include_router(analyze.router, prefix="/api")