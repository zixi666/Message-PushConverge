from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import create_access_token, get_current_user
from app.models import User
from app.schemas import (
    RegisterRequest, LoginRequest, ChangePasswordRequest,
    TokenResponse, R,
)

router = APIRouter(prefix="/auth", tags=["认证"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=R)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(username=req.username, password=pwd_ctx.hash(req.password))
    db.add(user)
    await db.commit()
    return R(msg="注册成功")


@router.post("/login", response_model=R)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not pwd_ctx.verify(req.password, user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = create_access_token({"sub": user.username})
    return R(data=TokenResponse(token=token).model_dump())


@router.post("/change_password", response_model=R)
async def change_password(
    req: ChangePasswordRequest,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not pwd_ctx.verify(req.old_password, user.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password = pwd_ctx.hash(req.new_password)
    await db.commit()
    return R(msg="密码修改成功")
