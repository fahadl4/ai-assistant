from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserRegistration, UserResponse
from app.schemas.permission import PermissionResponse, UserPermissionsUpdate
from app.core.permissions import require_permission
from app.services.user_service import assign_permissions_to_user, create_new_user, get_permissions_for_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/{target_user_id}/permissions", response_model=list[PermissionResponse])
async def get_specific_user_permissions(target_user_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_permissions_for_user(db, target_user_id, current_user)

@router.post("/new-user", response_model=UserResponse)
async def new_user(user_data: UserRegistration, db: AsyncSession = Depends(get_db), dependencies=[Depends(require_permission("manage_users"))]):
    return await create_new_user(db, user_data)

@router.post("/{target_user_id}/permissions", response_model=list[PermissionResponse])
async def assign_permissions(target_user_id: int, assign_permission: UserPermissionsUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await assign_permissions_to_user(db, target_user_id, assign_permission, current_user)