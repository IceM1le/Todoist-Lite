from fastapi import FastAPI

from app.api.v1.auth import router
app = FastAPI(
    title="Todoist Lite",
    description="Todo list",
    version="0.1.0"
)
app.include_router(router)

@app.get("/ping")
async def ping():
    return {"message": "pong"}
