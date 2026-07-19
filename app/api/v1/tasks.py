import datetime

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select, desc, asc, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskPatch, PaginatedTaskResponse

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


@router.get("", status_code=200, response_model=PaginatedTaskResponse)
async def get_tasks(page: int = 1,
                    limit: int = 10,
                    is_done: bool = None,
                    priority: str = None,
                    overdue: bool = None,
                    sort_by: str = "id",
                    order: str = "asc",
                    db=Depends(get_db), current_user=Depends(get_current_user)):
    query = select(Task).where(Task.owner_id == current_user.id)
    try:
        # Фильтр по is_done
        if is_done is not None:
            query = query.where(Task.is_done == is_done)

        # Фильтр по overdue
        if overdue:
            query = query.where(Task.due_date < datetime.datetime.now(datetime.UTC), Task.is_done == False)
        elif overdue == False:
            query = query.where(Task.due_date >= datetime.datetime.now(datetime.UTC), Task.is_done == True)

        # Фильтр по приоритету
        if priority is not None:
            if priority.isdigit() and 1 <= int(priority) <= 4:
                query = query.where(Task.priority == int(priority))
            else:
                raise HTTPException(status_code=400, detail="Invalid priority")

        sort_func = asc if order.lower() == "asc" else desc

        # Сортировка
        if sort_by == "title":
            query = query.order_by(sort_func(Task.title))
        elif sort_by == "priority":
            query = query.order_by(sort_func(Task.priority))
        elif sort_by == "due_date":
            query = query.order_by(sort_func(Task.due_date))
        elif sort_by == "is_done":
            query = query.order_by(sort_func(Task.is_done))
        elif sort_by == "id":
            query = query.order_by(sort_func(Task.id))
        else:
            query = query.order_by(sort_func(Task.id))  # сортировка по умолчанию
        # Пагинация
        query = query.offset((page - 1) * limit).limit(limit)
        result = await db.execute(query)

        items = result.scalars().all()
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(ex)}")
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit  # округление вверх
    }


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


async def edit_tasks(task_id, task_data, db, current_user):
    update_data = task_data.model_dump(exclude_unset=True)

    if 'title' in update_data:
        existing = await db.execute(
            select(Task).where(
                Task.title == update_data['title'],
                Task.owner_id == current_user.id,
                Task.id != task_id
            )
        )
        if existing.one_or_none():
            raise HTTPException(status_code=400, detail="Task already exists")

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner")

    for key, value in update_data.items():
        setattr(task, key, value)

    task.updated_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/{task_id}", status_code=200, response_model=TaskResponse)
async def put_task_id(task_id: int, task_create: TaskCreate, db=Depends(get_db),
                      current_user=Depends(get_current_user)):
    return await edit_tasks(task_id, task_create, db, current_user)


@router.patch("/{task_id}", status_code=200, response_model=TaskResponse)
async def put_task_id(task_id: int, task_patch: TaskPatch, db=Depends(get_db),
                      current_user=Depends(get_current_user)):
    return await edit_tasks(task_id, task_patch, db, current_user)


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
