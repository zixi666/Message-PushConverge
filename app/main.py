from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("message_push")

from app.database import async_engine
from app.models import Base
from app.routers.auth import router as auth_router
from app.routers.channels import router as channels_router
from app.routers.tasks import router as tasks_router
from app.routers.messages import router as messages_router
from app.routers.logs import router as logs_router
from app.routers.statistics import router as statistics_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()


# 第一步：先定义app变量！！！
app = FastAPI(title="Message-PushConverge", version="1.0.0", lifespan=lifespan)


# 第二步：再添加中间件（必须在app定义之后）
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    # 打印请求信息
    logger.info(f"收到请求 | 方法：{request.method} | 路径：{request.url.path} | 查询参数：{request.query_params}")
    # 尝试读取请求体（POST/PUT等）
    try:
        body = await request.body()
        if body:
            logger.info(f"请求体：{body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"读取请求体失败：{str(e)}")

    # 处理请求
    response = await call_next(request)

    # 打印响应信息
    process_time = time.time() - start_time
    logger.info(f"响应完成 | 状态码：{response.status_code} | 耗时：{process_time:.2f}s")
    return response


# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(channels_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")
app.include_router(statistics_router, prefix="/api/v1")

# 静态文件（Vue构建产物）
import os

web_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")
if os.path.isdir(web_dist):
    app.mount("/", StaticFiles(directory=web_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    # 启动时开启详细日志
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")