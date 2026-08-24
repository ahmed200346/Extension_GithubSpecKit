from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.schemas.task import TaskCreate
import uuid

async def create_task(db: AsyncSession, task_data: TaskCreate):
    db_task = Task(**task_data.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def get_task(db: AsyncSession, task_id: str):
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

async def update_task(db: AsyncSession, task_id: str, task_data: TaskCreate):
    db_task = await get_task(db, task_id)
    if db_task:
        for key, value in task_data.model_dump().items():
            setattr(db_task, key, value)
        await db.commit()
        await db.refresh(db_task)
    return db_task

async def update_task_status(db: AsyncSession, task_id: str, status: str):
    db_task = await get_task(db, task_id)
    if db_task:
        db_task.status = status
        await db.commit()
        await db.refresh(db_task)
    return db_task

async def delete_task(db: AsyncSession, task_id: str):
    db_task = await get_task(db, task_id)
    if db_task:
        await db.delete(db_task)
        await db.commit()
        return True
    return False
