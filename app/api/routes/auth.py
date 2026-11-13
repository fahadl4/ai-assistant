from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import InitialAdminSetup, UserResponse, TokenResponse, UserLogin
from app.services.user_service import create_initial_admin, login_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/setup-admin", response_model = UserResponse)
async def admin_setup(
    user_data: InitialAdminSetup,
    db: AsyncSession = Depends(get_db)
):
    return await create_initial_admin(db, user_data)

@router.post("/login", response_model = TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await login_user(db, user_data)

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user