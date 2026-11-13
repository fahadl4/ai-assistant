from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

#----------------Get user by email----------------

async def get_user_by_email(db: AsyncSession, user_email: str) -> User | None:
    result = await db.execute(
        select(User)
        .where(
            User.user_email == user_email,
            User.deleted_at.is_(None)
            )
        )
    existing_user = result.scalar_one_or_none()
    
    return existing_user

#--------------Get user count--------------

async def get_user_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(User).where(User.deleted_at.is_(None)))
    user_count = result.scalar_one()
    return user_count

#--------------Get user by id--------------

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User)
        .where(
            User.user_id == user_id,
            User.deleted_at.is_(None)
            )
        )
    user = result.scalar_one_or_none()
    return user

#--------------Create User-----------------

async def create_user(db: AsyncSession, user_name: str, user_email: str, hashed_password: str, role_id: int, is_super_admin: bool = False) -> User:
    existing_user = await get_user_by_email(db, user_email)
    
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists!"
        )
    
    new_user = User (
        user_name = user_name,
        user_email = user_email,
        hashed_password = hashed_password,
        role_id = role_id,
        is_super_admin = is_super_admin,
    )
    
    db.add(new_user)
    
    await db.flush()
    return new_user