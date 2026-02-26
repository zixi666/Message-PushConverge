from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import SendTask, SendTaskIns, SendWay
from app.schemas import (
    SendTaskCreate, SendTaskUpdate, SendTaskOut,
    SendTaskInsCreate, SendTaskInsOut, TaskInsDetail, R,
)

router = APIRouter(prefix="/sendtasks", tags=["任务管理"])


# ── 任务 CRUD ───────────────────────────────────────────
@router.post("/add", response_model=R)
async def add_task(
    req: SendTaskCreate,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = SendTask(
        id=SendTask.generate_id(),
        name=req.name,
        created_by=username,
        modified_by=username,
    )
    db.add(task)
    await db.commit()
    return R(msg="添加成功", data={"id": task.id})


@router.post("/edit", response_model=R)
async def edit_task(
    id: str,
    req: SendTaskUpdate,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SendTask).where(SendTask.id == id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if req.name is not None:
        task.name = req.name
    task.modified_by = username
    await db.commit()
    return R(msg="修改成功")


@router.post("/delete", response_model=R)
async def delete_task(
    id: str,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SendTask).where(SendTask.id == id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    await db.execute(delete(SendTaskIns).where(SendTaskIns.task_id == id))
    await db.delete(task)
    await db.commit()
    return R(msg="删除成功")


@router.get("/list", response_model=R)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str = Query(""),
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SendTask)
    count_query = select(func.count()).select_from(SendTask)
    if name:
        query = query.where(SendTask.name.like(f"%{name}%"))
        count_query = count_query.where(SendTask.name.like(f"%{name}%"))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(SendTask.created_on.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return R(data={
        "list": [SendTaskOut.model_validate(t).model_dump() for t in tasks],
        "total": total,
    })


@router.get("/get", response_model=R)
async def get_task(
    id: str,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SendTask).where(SendTask.id == id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return R(data=SendTaskOut.model_validate(task).model_dump())


# ── 实例 CRUD ───────────────────────────────────────────
@router.post("/ins/add", response_model=R)
async def add_ins(
        req: SendTaskInsCreate,
        username: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    # 校验任务存在
    task_res = await db.execute(select(SendTask).where(SendTask.id == req.task_id))
    if not task_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="任务不存在")

    # 校验渠道存在
    way_res = await db.execute(select(SendWay).where(SendWay.id == req.way_id))
    way = way_res.scalar_one_or_none()
    if not way:
        raise HTTPException(status_code=404, detail="渠道不存在")

    # 创建实例，不再需要 config 和 extra
    ins = SendTaskIns(
        id=SendTaskIns.generate_id(),
        task_id=req.task_id,
        way_id=req.way_id,
        way_type=way.type,
        content_type=req.content_type,
        created_by=username,
        modified_by=username,
    )
    db.add(ins)
    await db.commit()
    return R(msg="添加成功")

@router.post("/ins/delete", response_model=R)
async def delete_ins(
    id: str,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SendTaskIns).where(SendTaskIns.id == id))
    ins = result.scalar_one_or_none()
    if not ins:
        raise HTTPException(status_code=404, detail="实例不存在")
    await db.delete(ins)
    await db.commit()
    return R(msg="删除成功")


@router.post("/ins/update_enable", response_model=R)
async def update_ins_enable(
    id: str,
    enable: int,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SendTaskIns).where(SendTaskIns.id == id))
    ins = result.scalar_one_or_none()
    if not ins:
        raise HTTPException(status_code=404, detail="实例不存在")
    ins.enable = enable
    await db.commit()
    return R(msg="更新成功")


@router.get("/ins/gettask", response_model=R)
async def get_task_ins(
    id: str,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task_res = await db.execute(select(SendTask).where(SendTask.id == id))
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    ins_res = await db.execute(
        select(SendTaskIns).where(SendTaskIns.task_id == id).order_by(SendTaskIns.created_on.desc())
    )
    ins_list = ins_res.scalars().all()

    # 查询关联渠道名
    way_ids = list({i.way_id for i in ins_list})
    way_map: dict[str, str] = {}
    if way_ids:
        ways_res = await db.execute(select(SendWay).where(SendWay.id.in_(way_ids)))
        for w in ways_res.scalars().all():
            way_map[w.id] = w.name

    ins_out = []
    for i in ins_list:
        d = SendTaskInsOut.model_validate(i).model_dump()
        d["way_name"] = way_map.get(i.way_id, "")
        ins_out.append(d)

    return R(data=TaskInsDetail(id=task.id, name=task.name, ins_data=ins_out).model_dump())
