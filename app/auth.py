
import os
from uuid import uuid4, UUID
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status, Depends, Request
from jose import jwt, JWTError
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.database import get_db
from app.schemas import UserCreate
import aiosmtplib
from email.message import EmailMessage

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def send_token_email(email: EmailStr, token: str) -> None:
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = email
    msg["Subject"] = "А вот и твой токен для входа"
    msg.set_content(f"Токен для входа: {token}")

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER or None,
        password=SMTP_PASS or None,
        start_tls=False,
    )

async def get_or_create_user(db: AsyncSession, email: EmailStr) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def request_auth_token(email: EmailStr, db: AsyncSession) -> None:
    user = await get_or_create_user(db, email)
    token = create_access_token({"user_id": str(user.id)})
    await send_token_email(email, token)

def verify_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не валидный токен")
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ошибка валидации токена")

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не могу найти токен")
    token = auth_header.removeprefix("Bearer ").strip()
    payload = verify_token(token)
    user_id = payload["user_id"]
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Юзер не найден")
    return user
