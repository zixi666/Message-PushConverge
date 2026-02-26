import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import SendTask, SendTaskIns, SendWay, SendLog, SendStat
from app.schemas import SendMessageRequest, R
from app.services.dingtalk import DingTalkBot
from app.services.feishu import FeishuBot  # @NEW: 导入飞书机器人

router = APIRouter(prefix="/message", tags=["消息发送"])


@router.post("/send", response_model=R)
async def send_message(
        req: SendMessageRequest,
        request: Request,
        username: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    caller_ip = request.client.host if request.client else ""
    logs: list[str] = []
    status = 1  # 默认成功

    # 查询任务
    task_res = await db.execute(select(SendTask).where(SendTask.id == req.task_id))
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 查询实例
    ins_res = await db.execute(
        select(SendTaskIns).where(
            SendTaskIns.task_id == req.task_id,
            SendTaskIns.enable == 1,
        )
    )
    ins_list = ins_res.scalars().all()
    if not ins_list:
        raise HTTPException(status_code=400, detail="任务没有关联任何启用的实例")

    logs.append(f"开始任务[{req.task_id}]的发送")

    for idx, ins in enumerate(ins_list):
        # 查询渠道
        way_res = await db.execute(select(SendWay).where(SendWay.id == ins.way_id))
        way = way_res.scalar_one_or_none()
        if not way:
            logs.append(f"渠道[{ins.way_id}]信息不存在，跳过")
            status = 0
            continue

        logs.append(f">> 实例 {idx + 1}")
        logs.append(f"渠道名: {way.name}, 类型: {way.type}")

        auth_data = json.loads(way.auth) if way.auth else {}

        try:
            # @MODIFIED: 统一使用文本消息发送，不再判断内容类型
            if way.type == "dtalk":
                # 钉钉发送逻辑
                bot = DingTalkBot(
                    access_token=auth_data.get("access_token", ""),
                    secret=auth_data.get("secret", ""),
                )

                # @MODIFIED: 统一使用文本消息，优先使用text字段，如果没有则用title
                content = req.text or req.title or "无内容"
                await bot.send_text(content)
                logs.append(f"发送文本消息: {content[:50]}...")

            elif way.type == "feishu":
                # 飞书发送逻辑
                # 获取webhook_url
                webhook_url = auth_data.get("webhook_url")
                if not webhook_url and auth_data.get("access_token"):
                    webhook_url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{auth_data['access_token']}"

                bot = FeishuBot(
                    webhook_url=webhook_url,
                    secret=auth_data.get("secret", ""),
                )

                # @MODIFIED: 统一使用文本消息，优先使用text字段，如果没有则用title
                content = req.text or req.title or "无内容"
                await bot.send_text(content)
                logs.append(f"发送文本消息: {content[:50]}...")

            else:
                raise Exception(f"不支持的渠道类型: {way.type}")

            logs.append("发送成功！")
        except Exception as e:
            logs.append(f"发送失败：{str(e)}")
            status = 0

    # 写日志
    log_record = SendLog(
        task_id=req.task_id,
        name=task.name,
        log="\n".join(logs),
        status=status,
        caller_ip=caller_ip,
    )
    db.add(log_record)

    # 更新统计
    current_day = datetime.utcnow().strftime("%Y-%m-%d")
    stat_status = "success" if status == 1 else "failed"
    await db.execute(
        text(
            "INSERT INTO send_stats (task_id, day, status, num) "
            "VALUES (:task_id, :day, :status, 1) "
            "ON DUPLICATE KEY UPDATE num = num + 1"
        ),
        {"task_id": req.task_id, "day": current_day, "status": stat_status},
    )

    await db.commit()

    return R(
        msg="发送完成" if status == 1 else "发送过程中有失败",
        data={"log": "\n".join(logs), "status": status},
    )