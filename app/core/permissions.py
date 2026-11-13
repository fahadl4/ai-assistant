from fastapi import status, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.crud.permission import has_permission

def require_permission(permission_key: str):
    async def permission_checker(
        db: AsyncSession = Depends(get_db), 
        current_user: User = Depends(get_current_user)
    ):
        if current_user.is_super_admin:
            return current_user
        
        user_has_permission = await has_permission(db, current_user.user_id, permission_key)
        
        if not user_has_permission:
            raise HTTPException(
                status_code=403,
                detail="User is authenticated but lack this permission"
            )
        
        return current_user
    
    return permission_checker