from fastapi import APIRouter
from . import tasks, auth

router = APIRouter()

router.include_router(tasks.router)
router.include_router(auth.router)
