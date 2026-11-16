
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Row

from app.models.permission import Permission
from app.models.user_permission import UserPermission

from datetime import datetime, timezone


#-------------------- Get All User Permissions ------------------

async def get_user_permissions(db: AsyncSession, user_id: int) -> list[Row]:

    # Retrieve all active permission assignments for the specified user.
    # Join Permission to access permission_key and description.
    result = await db.execute(
        select(
            Permission.permission_key,
            Permission.description,
            UserPermission.is_enabled
        ).join(
            Permission,
            UserPermission.permission_id == Permission.permission_id
        ).where(
            # Only retrieve assignments belonging to the specified user.
            UserPermission.user_id == user_id,

            # Exclude soft-deleted user permission assignments.
            UserPermission.deleted_at.is_(None),

            # Exclude soft-deleted permission definitions.
            Permission.deleted_at.is_(None)
        )
    )

    # Retrieve all matching rows.
    # Each row contains permission_key, description and is_enabled.
    user_permissions = result.all()

    return user_permissions


#-------------------- Get Single User Permission ------------------

async def get_user_permission(
    db: AsyncSession,
    user_id: int,
    permission_id: int
) -> UserPermission | None:

    # Retrieve a specific permission assignment using user_id
    # and permission_id.
    result = await db.execute(
        select(UserPermission).where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id,

            # Only retrieve active assignments.
            UserPermission.deleted_at.is_(None)
        )
    )

    # Return the matching UserPermission object or None.
    user_permission = result.scalar_one_or_none()

    return user_permission


#-------------------- Create or Reactivate User Permission ------------------

async def create_user_permission(
    db: AsyncSession,
    user_id: int,
    permission_id: int,
    is_enabled: bool
) -> UserPermission:

    # Check whether an assignment already exists for this user
    # and permission.
    #
    # We intentionally don't filter by deleted_at because we also
    # need to find previously soft-deleted assignments.
    result = await db.execute(
        select(UserPermission).where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id
        )
    )

    existing_permission = result.scalar_one_or_none()

    # If an assignment already exists, update or reactivate it.
    if existing_permission:

        # Reactivate the assignment if it was previously deleted.
        if existing_permission.deleted_at is not None:
            existing_permission.deleted_at = None

        # Set the requested enabled/disabled status.
        existing_permission.is_enabled = is_enabled

        return existing_permission

    # If no assignment exists, create a new one.
    else:
        create_permission = UserPermission(
            user_id=user_id,
            permission_id=permission_id,
            is_enabled=is_enabled
        )

        # Add the new assignment to the current database session.
        db.add(create_permission)

        # Flush the INSERT without committing the transaction.
        await db.flush()

        return create_permission


#-------------------- Update User Permission ------------------

async def update_user_permission(
    db: AsyncSession,
    user_id: int,
    permission_id: int,
    is_enabled: bool
) -> UserPermission | None:

    # Retrieve the existing active permission assignment.
    user_permission = await get_user_permission(
        db,
        user_id,
        permission_id
    )

    # If no active assignment exists, return None.
    if user_permission is None:
        return None

    # Update the permission's enabled/disabled status.
    user_permission.is_enabled = is_enabled

    return user_permission


#-------------------- Delete User Permission ------------------

async def delete_user_permission(
    db: AsyncSession,
    user_id: int,
    permission_id: int
) -> UserPermission | None:

    # Retrieve the existing active permission assignment.
    user_permission = await get_user_permission(
        db,
        user_id,
        permission_id
    )

    # If no active assignment exists, return None.
    if user_permission is None:
        return None

    # Soft-delete the assignment instead of permanently
    # removing the database record.
    user_permission.deleted_at = datetime.now(timezone.utc)

    return user_permission
