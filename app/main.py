from fastapi import FastAPI

from app.api.v1 import router
app = FastAPI(
    title="Todoist Lite",
    description="Todo list",
    version="0.1.0"
)
app.include_router(router)

@app.get("", status_code=200)
async def index():
    return {"message": "Start page"}

@app.get("/ping", status_code=200)
async def ping():
    return {"message": "pong"}
