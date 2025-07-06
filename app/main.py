from fastapi import BackgroundTasks, HTTPException
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.game import start_game, process_hit, end_game
from app.state import user_game_state
from app.auth import request_auth_token, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import RequestCreate
from app.schemas import UserCreate, UserStats
import random


app = FastAPI()
security = HTTPBearer()

@app.post("/auth", status_code=202)
async def auth_request(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    background_tasks.add_task(request_auth_token, user.email, db)
    return {"Письмо с токеном отправлено на почту"}

@app.get("/me", response_model=UserStats, dependencies=[Depends(security)])
async def get_me(current_user: User = Depends(get_current_user)):
    return UserStats(
        id=current_user.id,
        email=current_user.email,
        total_requests=current_user.total_requests,
        successful_requests=current_user.successful_requests,
        failed_requests=current_user.failed_requests,
        last_request_at=current_user.last_request_at,
        success_rate=current_user.success_rate,
    )


@app.post("/start",  dependencies=[Depends(security)])
async def start(user: User = Depends(get_current_user)):
    answer = await start_game(user, None)
    user_game_state[user.id] = {"answer": answer, "streak": 0}
    print(f"[LOG] User {user.email} answer: {answer}")
    return {"message": "Игра начата", "holes": 7}

@app.post("/hit",  dependencies=[Depends(security)])
async def hit(
    req: RequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    state = user_game_state.get(user.id)
    if not state:
        raise HTTPException(status_code=400, detail="Сначала начните игру через /start")
    answer = state["answer"]
    streak = state["streak"]

    result = await process_hit(user, db, req.hit_value, answer, streak)
    if result["is_successful"]:
        state["streak"] += 1
    else:
        state["streak"] = 0
    new_answer = random.randint(0, 6)
    state["answer"] = new_answer
    print(f"[LOG] User {user.email} new answer: {new_answer}")

    return {
        "is_successful": result["is_successful"],
        "points": result["points"],
        "streak": state["streak"],
        "success_rate": result["success_rate"],
        "total_requests": result["total_requests"],
        "successful_requests": result["successful_requests"],
        "failed_requests": result["failed_requests"],
        "last_request_at": result["last_request_at"],
    }


@app.post("/end", dependencies=[Depends(security)])
async def end(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await end_game(user, db)