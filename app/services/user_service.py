
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password

from app.crud.permission import get_permission_by_key, has_permission
from app.crud.role import get_role_by_id, get_role_by_title
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_count,
    get_user_by_id
)
from app.crud.user_permission import create_user_permission, get_user_permissions

from app.models.user import User
from app.models.permission import Permission
from app.models.user_permission import UserPermission

from app.schemas.user import InitialAdminSetup, UserLogin, UserRegistration
from app.schemas.permission import PermissionResponse, UserPermissionsUpdate


#---------------- Creates First User as Super Admin -----------------

async def create_initial_admin(db: AsyncSession, user_data: InitialAdminSetup):

    # ---------- Verify Initial Admin Setup Secret ----------
    # Make sure the supplied setup secret matches the secret
    # configured in the application's environment variables.
    if settings.INITIAL_ADMIN_SETUP_SECRET != user_data.setup_secret:
        raise HTTPException(
            status_code=403,
            detail="Invalid Admin Setup Secret!"
        )

    try:
        # ---------- Transaction-Level Advisory Lock ----------
        # Prevent multiple requests from creating the initial
        # Super Admin simultaneously.
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": 123456789}
        )

        # ---------- Check Existing Users ----------
        # Only allow initial setup if no active users exist.
        user_count = await get_user_count(db)

        if user_count:
            raise HTTPException(
                status_code=409,
                detail="Initial admin has already been created"
            )

        # ---------- Retrieve Admin Role ----------
        # Find the Admin role that will be assigned to
        # the initial Super Admin.
        admin_role = await get_role_by_title(db, "Admin")

        if not admin_role:
            raise HTTPException(
                status_code=500,
                detail="Admin role doesn't exist"
            )

        # ---------- Hash Password ----------
        # Never store the user's plain-text password.
        hashed_password = hash_password(user_data.password)

        # ---------- Create Super Admin ----------
        # Create the first user and mark them as Super Admin.
        new_user = await create_user(
            db,
            user_data.user_name,
            user_data.user_email,
            hashed_password,
            admin_role.role_id,
            is_super_admin=True
        )

        # ---------- Assign All Existing Permissions ----------
        # Retrieve all active permission definitions.
        result = await db.execute(select(Permission))
        permissions = result.scalars().all()

        # Assign every existing permission to the initial Super Admin.
        for permission in permissions:
            user_permission = UserPermission(
                user_id=new_user.user_id,
                permission_id=permission.permission_id,
                is_enabled=True
            )
            db.add(user_permission)

        # ---------- Commit Transaction ----------
        # Save the Super Admin and all permission assignments together.
        await db.commit()

    except Exception:
        # If any operation fails, undo all changes in this transaction.
        await db.rollback()
        raise

    # ---------- Refresh User Object ----------
    # Reload the committed user data from the database.
    await db.refresh(new_user)

    return new_user


#---------------- User Login -----------------

async def login_user(db: AsyncSession, user_data: UserLogin):

    # ---------- Retrieve User ----------
    # Find an active user using their email address.
    existing_user = await get_user_by_email(db, user_data.user_email)

    # If the email doesn't exist, reject the login.
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # ---------- Verify Password ----------
    # Compare the submitted password with the stored password hash.
    password = verify_password(
        user_data.password,
        existing_user.hashed_password
    )

    if not password:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # ---------- Generate Access Token ----------
    # Create a JWT access token for the authenticated user.
    token = create_access_token(existing_user.user_id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


#---------------- Create New User -----------------

async def create_new_user(db: AsyncSession, user_data: UserRegistration):

    try:
        # ---------- Retrieve and Validate Role ----------
        # Make sure the requested role exists and is active.
        role = await get_role_by_id(db, user_data.role_id)

        if role is None:
            raise HTTPException(
                status_code=404,
                detail="Role Not Found!"
            )

        # ---------- Hash Password ----------
        # Hash the password before storing it.
        hashed_password = hash_password(user_data.password)

        # ---------- Create User ----------
        # New users are never allowed to become Super Admin
        # through the normal user creation process.
        new_user = await create_user(
            db,
            user_data.user_name,
            user_data.user_email,
            hashed_password,
            role.role_id,
            is_super_admin=False
        )

        # ---------- Commit Transaction ----------
        await db.commit()

    except Exception:
        # Roll back the transaction if any operation fails.
        await db.rollback()
        raise

    # ---------- Refresh User Object ----------
    # Refresh only after a successful commit.
    await db.refresh(new_user)

    return new_user


#---------------- Get Permissions For User -----------------

async def get_permissions_for_user(
    db: AsyncSession,
    target_user_id: int,
    current_user: User
):

    # ---------- Get Target User ----------
    # Retrieve the user whose permissions are being requested.
    target_user = await get_user_by_id(db, target_user_id)

    # Check whether the target user exists.
    # If not, return a 404 Not Found error.
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found!"
        )
    if target_user.is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="You can't see the permissions of super admin"
        )

    # ---------- Check Authorization ----------
    # Users can view their own permissions without requiring
    # the manage_permissions permission.
    #
    # Super Admin can view any user's permissions without
    # requiring an additional permission.
    #
    # Other users must have manage_permissions to view
    # someone else's permissions.
    if (
        current_user.user_id != target_user.user_id
        and not current_user.is_super_admin
    ):
        has_access = await has_permission(
            db,
            current_user.user_id,
            "manage_permissions"
        )

        # If the requester doesn't have the required permission,
        # deny access with a 403 Forbidden error.
        if has_access is False:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to view this user's permissions."
            )

    # ---------- Retrieve Target User Permissions ----------
    # Fetch all active permission assignments belonging to
    # the target user.
    permissions = await get_user_permissions(
        db,
        target_user.user_id
    )

    # ---------- Convert Database Rows to Response Schema ----------
    # Convert each SQLAlchemy result row into a PermissionResponse
    # object so FastAPI can return the expected response structure.
    return [
        PermissionResponse(**row._mapping)
        for row in permissions
    ]


async def assign_permissions_to_user(
    db: AsyncSession,
    target_user_id: int,
    update_permissions: UserPermissionsUpdate,
    current_user: User
):
    # Retrieve the user whose permissions we want to update.
    target_user = await get_user_by_id(db, target_user_id)

    # Check whether the target user exists.
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found!"
        )

    # Prevent users from modifying their own permissions.
    if target_user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="You can't update your own permissions"
        )

    # Protect the Super Admin's permissions from modification.
    if target_user.is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="You can't assign permissions to Super Admin"
        )

    # Super Admin can bypass the manage_permissions check.
    # All other users must have this permission.
    if not current_user.is_super_admin:
        has_access = await has_permission(
            db,
            current_user.user_id,
            "manage_permissions"
        )

        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to assign permissions."
            )

    try:
        # Process each permission submitted in the request.
        for permission in update_permissions.permissions:

            # Find the permission definition using its unique key.
            permission_record = await get_permission_by_key(
                db,
                permission.permission_key
            )

            # Reject the request if the permission doesn't exist
            # or has been soft-deleted.
            if permission_record is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Permission '{permission.permission_key}' doesn't exist."
                )

            # Create or update the user's permission assignment.
            await create_user_permission(
                db,
                target_user.user_id,
                permission_record.permission_id,
                permission.is_enabled
            )

        # Commit all permission changes together after the loop.
        await db.commit()
        updated_user_permissions = await get_user_permissions(db, target_user.user_id)
        
        return [
            PermissionResponse(**row._mapping)
             for row in updated_user_permissions
        ]

    except Exception:
        # Roll back all changes if anything goes wrong.
        await db.rollback()
        raise