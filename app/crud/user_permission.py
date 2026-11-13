from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_permission import UserPermission

from datetime import datetime, timezone


#--------------------All User Permissions------------------
async def get_user_permissions(db: AsyncSession, user_id: int) -> list[UserPermission]:
    result = await db.execute(
        select(UserPermission)
        .where(
            UserPermission.user_id == user_id,
            UserPermission.deleted_at.is_(None)
        )
    )
    user_permissions = result.scalars().all()
    return user_permissions

#--------------------All Single User Permission------------------

async def get_user_permission(db: AsyncSession, user_id: int, permission_id: int) -> UserPermission | None:
    result = await db.execute(
        select(UserPermission)
        .where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id,
            UserPermission.deleted_at.is_(None)
        )
    )
    user_permission = result.scalar_one_or_none()
    return user_permission

#--------------------Create User Permission------------------

async def create_user_permission(db: AsyncSession, user_id: int, permission_id: int, is_enabled: bool) -> UserPermission:
    result = await db.execute(
        select(UserPermission)
        .where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id
        )
    )
    existing_permission = result.scalar_one_or_none()
    
    if existing_permission:
        if existing_permission.deleted_at is not None:
            existing_permission.deleted_at = None

        existing_permission.is_enabled = is_enabled
        
        return existing_permission
    else:
        create_permission = UserPermission(
            user_id = user_id,
            permission_id = permission_id,
            is_enabled = is_enabled
        )
        
        db.add(create_permission)
        await db.flush()
        
        return create_permission
    
async def update_user_permission(db: AsyncSession, user_id: int, permission_id: int, is_enabled: bool) -> UserPermission | None:
    user_permission = await get_user_permission(db, user_id, permission_id)
    
    if user_permission is None:
        return None
    
    user_permission.is_enabled = is_enabled
    
    return user_permission

async def delete_user_permission(db: AsyncSession, user_id: int, permission_id: int) -> UserPermission | None:
    user_permission = await get_user_permission(db, user_id, permission_id)
    
    if user_permission is None:
        return None
    
    user_permission.deleted_at = datetime.now(timezone.utc)
    
    return user_permission