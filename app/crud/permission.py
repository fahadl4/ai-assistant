from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.user_permission import UserPermission


# ---------- Get Permission By Key ----------

async def get_permission_by_key(
    db: AsyncSession,
    permission_key: str
) -> Permission | None:

    # Retrieve the permission matching the provided permission key.
    # Select the complete Permission model rather than individual columns.
    result = await db.execute(
        select(Permission).where(
            # Find the permission using its unique key.
            Permission.permission_key == permission_key,

            # Exclude permissions that have been soft-deleted.
            Permission.deleted_at.is_(None)
        )
    )

    # Return the matching Permission object.
    # If no active permission exists, return None.
    permission = result.scalar_one_or_none()

    return permission


# ---------- Check User Permission ----------

async def has_permission(
    db: AsyncSession,
    user_id: int,
    permission_key: str
) -> bool:

    # Retrieve the user's permission assignment by joining
    # UserPermission with Permission.
    #
    # UserPermission contains the user_id and permission_id.
    # Permission contains the permission_key.
    result = await db.execute(
        select(UserPermission)
        .join(
            Permission,
            Permission.permission_id == UserPermission.permission_id
        )
        .where(
            # Check the permission assignment for the requested user.
            UserPermission.user_id == user_id,

            # Match the requested permission key.
            Permission.permission_key == permission_key,

            # Only allow permissions that are enabled.
            UserPermission.is_enabled.is_(True),

            # Exclude soft-deleted user permission assignments.
            UserPermission.deleted_at.is_(None),

            # Exclude soft-deleted permission definitions.
            Permission.deleted_at.is_(None)
        )
    )

    # Retrieve one matching assignment or None.
    user_has_permission = result.scalar_one_or_none()

    # Return True if an active, enabled assignment exists.
    # Otherwise, return False.
    return user_has_permission is not None
