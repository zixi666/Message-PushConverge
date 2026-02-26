from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import SendLog
from app.schemas import SendLogOut, R

router = APIRouter(prefix="/sendlogs", tags=["发送日志"])


@router.get("/list", response_model=R)
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str = Query(""),
    task_id: str = Query(""),
    status: int = Query(-1),
    day: str = Query(""),
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SendLog)
    count_query = select(func.count()).select_from(SendLog)

    if name:
        query = query.where(SendLog.name.like(f"%{name}%"))
        count_query = count_query.where(SendLog.name.like(f"%{name}%"))
    if task_id:
        query = query.where(SendLog.task_id == task_id)
        count_query = count_query.where(SendLog.task_id == task_id)
    if status >= 0:
        query = query.where(SendLog.status == status)
        count_query = count_query.where(SendLog.status == status)
    if day:
        query = query.where(func.date(SendLog.created_on) == day)
        count_query = count_query.where(func.date(SendLog.created_on) == day)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(SendLog.created_on.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return R(data={
        "list": [SendLogOut.model_validate(lg).model_dump() for lg in logs],
        "total": total,
    })
