from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import SendStat
from app.schemas import DailyStat, StatisticOut, R

router = APIRouter(prefix="/statistic", tags=["数据统计"])


@router.get("", response_model=R)
async def get_statistics(
    days: int = Query(30, ge=1, le=365),
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_day = datetime.utcnow().strftime("%Y-%m-%d")

    # 今日统计
    today_res = await db.execute(
        select(
            func.coalesce(func.sum(case((SendStat.status == "success", SendStat.num), else_=0)), 0).label("succ"),
            func.coalesce(func.sum(case((SendStat.status == "failed", SendStat.num), else_=0)), 0).label("fail"),
            func.coalesce(func.sum(SendStat.num), 0).label("total"),
        ).where(SendStat.day == current_day)
    )
    today_row = today_res.one()

    # 总计
    total_res = await db.execute(
        select(func.coalesce(func.sum(SendStat.num), 0).label("total"))
    )
    total_num = total_res.scalar() or 0

    # 每日趋势
    past_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    daily_res = await db.execute(
        select(
            SendStat.day,
            func.coalesce(func.sum(case((SendStat.status == "success", SendStat.num), else_=0)), 0).label("succ_num"),
            func.coalesce(func.sum(case((SendStat.status == "failed", SendStat.num), else_=0)), 0).label("failed_num"),
            func.coalesce(func.sum(SendStat.num), 0).label("total_num"),
        ).where(SendStat.day >= past_date)
        .group_by(SendStat.day)
        .order_by(SendStat.day)
    )
    daily_stats = [
        DailyStat(day=row.day, succ_num=int(row.succ_num), failed_num=int(row.failed_num), total_num=int(row.total_num))
        for row in daily_res.all()
    ]

    out = StatisticOut(
        today_succ_num=int(today_row.succ),
        today_failed_num=int(today_row.fail),
        today_total_num=int(today_row.total),
        total_num=int(total_num),
        daily_stats=daily_stats,
    )
    return R(data=out.model_dump())


@router.get("/task", response_model=R)
async def get_task_statistics(
    task_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_day = datetime.utcnow().strftime("%Y-%m-%d")

    today_res = await db.execute(
        select(
            func.coalesce(func.sum(case((SendStat.status == "success", SendStat.num), else_=0)), 0).label("succ"),
            func.coalesce(func.sum(case((SendStat.status == "failed", SendStat.num), else_=0)), 0).label("fail"),
            func.coalesce(func.sum(SendStat.num), 0).label("total"),
        ).where(SendStat.day == current_day, SendStat.task_id == task_id)
    )
    today_row = today_res.one()

    total_res = await db.execute(
        select(func.coalesce(func.sum(SendStat.num), 0).label("total"))
        .where(SendStat.task_id == task_id)
    )
    total_num = total_res.scalar() or 0

    past_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    daily_res = await db.execute(
        select(
            SendStat.day,
            func.coalesce(func.sum(case((SendStat.status == "success", SendStat.num), else_=0)), 0).label("succ_num"),
            func.coalesce(func.sum(case((SendStat.status == "failed", SendStat.num), else_=0)), 0).label("failed_num"),
            func.coalesce(func.sum(SendStat.num), 0).label("total_num"),
        ).where(SendStat.day >= past_date, SendStat.task_id == task_id)
        .group_by(SendStat.day)
        .order_by(SendStat.day)
    )
    daily_stats = [
        DailyStat(day=row.day, succ_num=int(row.succ_num), failed_num=int(row.failed_num), total_num=int(row.total_num))
        for row in daily_res.all()
    ]

    out = StatisticOut(
        today_succ_num=int(today_row.succ),
        today_failed_num=int(today_row.fail),
        today_total_num=int(today_row.total),
        total_num=int(total_num),
        daily_stats=daily_stats,
    )
    return R(data=out.model_dump())
