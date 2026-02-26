import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import SendWay, SendTaskIns
from app.schemas import SendWayCreate, SendWayUpdate, SendWayOut, R
from app.services.dingtalk import DingTalkBot

router = APIRouter(prefix="/sendways", tags=["渠道管理"])


@router.post("/add", response_model=R)
async def add_way(
        req: SendWayCreate,
        username: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    # @MODIFIED: 根据类型构建不同的auth数据
    if req.type == "dtalk":
        if not req.access_token:
            raise HTTPException(status_code=400, detail="钉钉渠道需要access_token")
        auth_data = {
            "access_token": req.access_token,
            "secret": req.secret or ""
        }
    elif req.type == "feishu":
        # @NEW: 飞书渠道
        if not req.access_token:
            raise HTTPException(status_code=400, detail="飞书渠道需要access_token")

        # 自动构建飞书webhook_url
        webhook_url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{req.access_token}"
        auth_data = {
            "access_token": req.access_token,
            "webhook_url": webhook_url,
            "secret": req.secret or ""
        }
    else:
        raise HTTPException(status_code=400, detail="不支持的渠道类型")

    way = SendWay(
        id=SendWay.generate_id(),
        name=req.name,
        type=req.type,  # @NEW: 保存渠道类型
        auth=json.dumps(auth_data),
        created_by=username,
        modified_by=username,
    )
    db.add(way)
    await db.commit()
    return R(msg="添加成功")


@router.post("/edit", response_model=R)
async def edit_way(
        id: str,
        req: SendWayUpdate,
        username: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SendWay).where(SendWay.id == id))
    way = result.scalar_one_or_none()
    if not way:
        raise HTTPException(status_code=404, detail="渠道不存在")

    if req.name is not None:
        way.name = req.name

    # @MODIFIED: 根据渠道类型更新不同的认证信息
    auth_data = json.loads(way.auth) if way.auth else {}

    if way.type == "dtalk":
        if req.access_token is not None:
            auth_data["access_token"] = req.access_token
        if req.secret is not None:
            auth_data["secret"] = req.secret
    elif way.type == "feishu":
        # @NEW: 更新飞书认证信息
        if req.access_token is not None:
            auth_data["access_token"] = req.access_token
            # 同时更新webhook_url
            auth_data["webhook_url"] = f"https://open.feishu.cn/open-apis/bot/v2/hook/{req.access_token}"
        if req.secret is not None:
            auth_data["secret"] = req.secret

    way.auth = json.dumps(auth_data)
    way.modified_by = username
    await db.commit()
    return R(msg="修改成功")


@router.post("/test", response_model=R)
async def test_way(
        id: str,
        username: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SendWay).where(SendWay.id == id))
    way = result.scalar_one_or_none()
    if not way:
        raise HTTPException(status_code=404, detail="渠道不存在")

    auth_data = json.loads(way.auth)

    try:
        if way.type == "dtalk":
            from app.services.dingtalk import DingTalkBot
            bot = DingTalkBot(
                access_token=auth_data.get("access_token", ""),
                secret=auth_data.get("secret", ""),
            )
            await bot.send_text("Message-Push-Nest 渠道测试消息")

        elif way.type == "feishu":
            # @NEW: 测试飞书渠道
            from app.services.feishu import FeishuBot

            # 获取webhook_url
            webhook_url = auth_data.get("webhook_url")
            if not webhook_url and auth_data.get("access_token"):
                webhook_url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{auth_data['access_token']}"

            bot = FeishuBot(
                webhook_url=webhook_url,
                secret=auth_data.get("secret", ""),
            )
            await bot.send_text("Message-Push-Nest 渠道测试消息")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return R(msg="测试消息发送成功")


@router.get("/list", response_model=R)
async def list_ways(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        name: str = Query(""),
        username: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    query = select(SendWay)
    count_query = select(func.count()).select_from(SendWay)
    if name:
        query = query.where(SendWay.name.like(f"%{name}%"))
        count_query = count_query.where(SendWay.name.like(f"%{name}%"))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(SendWay.created_on.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    ways = result.scalars().all()

    # @MODIFIED: 处理返回数据
    way_list = []
    for w in ways:
        way_dict = SendWayOut.model_validate(w).model_dump()
        # 解析auth字段
        auth_data = json.loads(w.auth) if w.auth else {}
        # 添加前端需要的字段
        way_dict["access_token"] = auth_data.get("access_token", "")
        way_dict["has_secret"] = bool(auth_data.get("secret"))
        way_list.append(way_dict)

    return R(data={
        "list": way_list,
        "total": total,
    })