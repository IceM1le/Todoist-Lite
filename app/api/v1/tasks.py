import datetime

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskPatch

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", status_code=201, response_model=TaskResponse)
async def create_task(task_create: TaskCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    already_exists = await db.execute(select(Task).where(
        Task.title == task_create.title, Task.owner_id == current_user.id))
    if already_exists.one_or_none():
        raise HTTPException(status_code=400, detail="Task already exists")
    task = Task(
        title=task_create.title,
        description=task_create.description,
        priority=task_create.priority,
        is_done=task_create.is_done,
        due_date=task_create.due_date,
        owner_id=current_user.id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("", status_code=200)
async def get_tasks(page: int = 1, limit: int = 10, is_done: str = None,
                    priority: str = None, overdue: str = None, sort_by: str = "id",
                    db=Depends(get_db), current_user=Depends(get_current_user)):
    query = select(Task).where(Task.owner_id == current_user.id)

    is_done_bool = None
    if is_done is not None:
        is_done_bool = is_done.lower() == "true"

    overdue_bool = None
    if overdue is not None:
        overdue_bool = overdue.lower() == "true"

    # Фильтр по is_done
    if is_done_bool is not None:
        query = query.where(Task.is_done == is_done_bool)

    # Фильтр по overdue
    if overdue_bool:
        query = query.where(Task.due_date < datetime.datetime.now(datetime.UTC))
    elif overdue_bool == False:
        query = query.where(Task.due_date > datetime.datetime.now(datetime.UTC))

    # Фильтр по приоритету
    if priority and priority.isdigit() and 1 <= int(priority) <= 4:
        query = query.where(Task.priority == int(priority))

    # Сортировка
    if sort_by == "title":
        query = query.order_by(Task.title)
    elif sort_by == "priority":
        query = query.order_by(Task.priority)
    elif sort_by == "due_date":
        query = query.order_by(Task.due_date)
    elif sort_by == "is_done":
        query = query.order_by(Task.is_done)
    else:
        query = query.order_by(Task.id)  # сортировка по умолчанию

    # Пагинация
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{task_id}", status_code=200, response_model=TaskResponse)
async def get_task_id(task_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id == current_user.id:
        return task
    else:
        raise HTTPException(status_code=403, detail="You are not the owner of the task")


@router.put("/{task_id}", status_code=200, response_model=TaskResponse)
async def put_task_id(task_id: int, task_create: TaskCreate, db=Depends(get_db),
                      current_user=Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id == current_user.id:
        task.title = task_create.title
        task.description = task_create.description
        task.priority = task_create.priority
        task.due_date = task_create.due_date
        task.is_done = task_create.is_done
        task.updated_at = datetime.datetime.now(datetime.UTC)
        await db.commit()
        await db.refresh(task)
        return task
    else:
        raise HTTPException(status_code=403, detail="You are not the owner of the task")


@router.patch("/{task_id}", status_code=200, response_model=TaskResponse)
async def put_task_id(task_id: int, task_patch: TaskPatch, db=Depends(get_db),
                      current_user=Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id == current_user.id:
        task.priority = task_patch.priority
        task.due_date = task_patch.due_date
        task.is_done = task_patch.is_done
        task.updated_at = datetime.datetime.now(datetime.UTC)
        await db.commit()
        await db.refresh(task)
        return task
    else:
        raise HTTPException(status_code=403, detail="You are not the owner of the task")

@router.delete("/{task_id}", status_code=204)
async def get_task_id(task_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id == current_user.id:
        await db.delete(task)
        await db.commit()
        return None
    else:
        raise HTTPException(status_code=403, detail="You are not the owner of the task")

