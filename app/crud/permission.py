from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.user_permission import UserPermission

async def has_permission(db: AsyncSession, user_id: int, permission_key: str) -> bool:
    result = await db.execute(
        select(UserPermission)
        .join(Permission, Permission.permission_id == UserPermission.permission_id)
        .where(
            UserPermission.user_id == user_id,
            Permission.permission_key == permission_key,
            UserPermission.is_enabled.is_(True),
            UserPermission.deleted_at.is_(None),
            Permission.deleted_at.is_(None)
        )
    )
    user_has_permission = result.scalar_one_or_none()
    return user_has_permission is not None