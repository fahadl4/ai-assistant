from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, PrimaryKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.permission import Permission

class UserPermission(Base):
    __tablename__ = "user_permissions"
    
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "permission_id"),
    )
    
    user_id: Mapped[int] = mapped_column(
       ForeignKey("users.user_id"),
       nullable=False 
    )
    
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.permission_id"),
        nullable=False
    )
    
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
        
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
        
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    user: Mapped["User"] = relationship(
        back_populates="user_permissions"
    )
    
    permission: Mapped["Permission"] = relationship(
        back_populates="user_permissions"
    )