from app.core.celery_app import celery_app

@celery_app.task
def add(a: int, b: int) -> int:
    return a + b

@celery_app.task
def _():
    pass