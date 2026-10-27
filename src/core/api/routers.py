from fastapi import APIRouter

from src.tasks.api import tasks_router, user_tasks_router
from src.users.api import users_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(user_tasks_router)
api_router.include_router(tasks_router)
