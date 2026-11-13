from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role

#----------Get Role By Title-----------

async def get_role_by_title(db: AsyncSession, role_title: str) -> Role | None:
    result =  await db.execute(
        select(Role)
        .where(Role.role_title == role_title, Role.deleted_at.is_(None))
        )
    role = result.scalar_one_or_none()
    return role

#----------Get Role By ID-----------

async def get_role_by_id(db: AsyncSession, role_id: int) -> Role | None:
    result = await db.execute(
        select(Role)
        .where(
            Role.role_id == role_id,
            Role.deleted_at.is_(None)
        )
    )
    role = result.scalar_one_or_none()
    
    return role