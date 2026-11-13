from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role

#----------Get Role Title-----------

async def get_role_by_title(db: AsyncSession, role_title: str) -> Role | None:
    result =  await db.execute(
        select(Role)
        .where(Role.role_title == role_title)
        )
    role = result.scalar_one_or_none()
    return role