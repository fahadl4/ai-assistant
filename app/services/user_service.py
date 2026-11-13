from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.crud.role import get_role_by_id, get_role_by_title
from app.crud.user import create_user, get_user_by_email, get_user_count
from app.schemas.user import InitialAdminSetup, UserLogin, UserRegistration
from app.models.permission import Permission
from app.models.user_permission import UserPermission

#---------------- Creates First User as Super Admin -----------------
async def create_initial_admin(db: AsyncSession, user_data: InitialAdminSetup):
    if settings.INITIAL_ADMIN_SETUP_SECRET != user_data.setup_secret:
        raise HTTPException(
            status_code=403,
            detail="Invalid Admin Setup Secret!"
        )
    try:
        #---------------- Transaction-level advisory lock -----------------
        await db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": 123456789})
        #------------------------------------------------------------------
        
        user_count = await get_user_count(db)
        if user_count:
            raise HTTPException(
                status_code=409,
                detail="Initial admin has already been created"
            )
    
        admin_role = await get_role_by_title(db, "Admin")
        if not admin_role:
            raise HTTPException(
                status_code=500,
                detail="Admin role doesn't exist"
            )
    
        hashed_password = hash_password(user_data.password)
    
        new_user = await create_user(db, user_data.user_name, user_data.user_email, hashed_password, admin_role.role_id, is_super_admin = True)
        
        #---------------- Adding User Permission -----------------
        result = await db.execute(select(Permission))
        permissions = result.scalars().all()
        
        for permission in permissions:
            user_permission = UserPermission(
                user_id = new_user.user_id,
                permission_id = permission.permission_id,
                is_enabled = True
            )
            db.add(user_permission) 
    
        await db.commit()
        
    except Exception:
        await db.rollback()
        await db.refresh(new_user)
        raise
        
    return new_user

async def login_user(db: AsyncSession, user_data: UserLogin):
    existing_user = await get_user_by_email(db, user_data.user_email)
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
        
    password = verify_password(user_data.password, existing_user.hashed_password)
    
    if not password:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    token = create_access_token(existing_user.user_id)
    
    return {
        "access_token": token,
        "token_type": "bearer"
    }
    
async def create_new_user(db: AsyncSession, user_data: UserRegistration):
    try:
        role = await get_role_by_id(db, user_data.role_id)
        if role is None:
            raise HTTPException(
                status_code=404,
                detail="Role Not Found!"
            )
        hashed_password = hash_password(user_data.password)
        # database operations
        new_user = await create_user(db, user_data.user_name, user_data.user_email, hashed_password, role.role_id, is_super_admin = False)
        await db.commit()
        
    except Exception:
        await db.rollback()
        await db.refresh(new_user)
        raise
    
    return new_user