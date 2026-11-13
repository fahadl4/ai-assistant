from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.db.seed_constants import roles, permissions

async def seed_roles():
    async with AsyncSessionLocal() as db:
        
        for title in roles:
            result = await db.execute(select(Role).where(Role.role_title == title))
            existing_role = result.scalar_one_or_none()
            
            if existing_role is None:
                db.add(Role(role_title = title))
        
        await db.commit()

async def seed_permissions():
    async with AsyncSessionLocal() as db:
        for permission in permissions:
            result = await db.execute(
                select(Permission)
                .where(Permission.permission_key == permission["permission_key"])
            )
            existing_permission = result.scalar_one_or_none()
            
            if existing_permission is None:
                db.add(Permission(permission_key = permission["permission_key"], description = permission["description"]))
        
        await db.commit()

async def main():
    await seed_roles()
    await seed_permissions()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())