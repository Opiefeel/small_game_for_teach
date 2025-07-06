
import random
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Request
from .schemas import RequestCreate
from sqlalchemy import select, func
from .state import user_game_state


# Очки за успешные удары: 2, 4, 8, 16 (по порядку)
POINTS_SEQUENCE = [2, 4, 8, 16]

def get_points_for_streak(streak: int) -> int:
    idx = min(streak, len(POINTS_SEQUENCE)) - 1
    return POINTS_SEQUENCE[idx] if idx >= 0 else 2

async def start_game(user: User, db: AsyncSession) -> int:
    answer = random.randint(0, 6)
    return answer

async def process_hit(
    user: User,
    db: AsyncSession,
    hit_value: int,
    answer: int,
    prev_streak: int
) -> dict:
    is_successful = hit_value == answer
    now = datetime.utcnow()

    streak = prev_streak + 1 if is_successful else 0
    points = get_points_for_streak(streak) if is_successful else 0

    user.total_requests += 1
    if is_successful:
        user.successful_requests += 1
    else:
        user.failed_requests += 1
    user.last_request_at = now
    user.success_rate = (
        user.successful_requests / user.total_requests if user.total_requests else 0.0
    )

    req = Request(
        user_id=user.id,
        hit_value=hit_value,
        points=points,
        is_successful=is_successful,
        created_at=now,
    )
    db.add(req)
    await db.commit()
    await db.refresh(user)

    return {
        "is_successful": is_successful,
        "points": points,
        "streak": streak if is_successful else 0,
        "success_rate": user.success_rate,
        "total_requests": user.total_requests,
        "successful_requests": user.successful_requests,
        "failed_requests": user.failed_requests,
        "last_request_at": user.last_request_at,
    }


async def end_game(user: User, db: AsyncSession) -> dict:
    result = await db.execute(
        select(func.sum(Request.points)).where(Request.user_id == user.id)
    )
    total_points = result.scalar() or 0
    user_game_state.pop(user.id, None)
    return {
        "message": "Игра завершена",
        "final_score": total_points,
        "stats": {
            "total_requests": user.total_requests,
            "successful_requests": user.successful_requests,
            "failed_requests": user.failed_requests,
            "last_request_at": user.last_request_at,
            "success_rate": user.success_rate,
        }
    }