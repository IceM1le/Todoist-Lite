from fastapi import FastAPI
from app.core.config import settings

# Создаём экземпляр приложения
app = FastAPI(
    title="Todoist Lite",
    description="Todo list",
    version="0.1.0"
)

@app.get("/ping")
async def ping():
    return {"message": "pong", "secret_loaded": bool(settings.secret_key)}