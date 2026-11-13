from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.user import UserRegistration, UserResponse
from app.core.permissions import require_permission
from app.services.user_service import create_new_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_permission("manage_users"))]
)

@router.post("/new-user", response_model=UserResponse)
async def new_user(user_data: UserRegistration, db: AsyncSession = Depends(get_db)):
    return await create_new_user(db, user_data)