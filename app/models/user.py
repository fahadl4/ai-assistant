from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.user_permission import UserPermission

class User(Base):
    __tablename__ = "users"
    
    __table_args__ = (
        Index(
            "uq_active_user_email",
            "user_email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL")
        ),
        Index(
            "uq_single_active_super_admin",
            "is_super_admin",
            unique=True,
            postgresql_where=text(
                "is_super_admin IS TRUE AND deleted_at IS NULL"
            )
        ),
    )
    
    user_id: Mapped[int] = mapped_column(
        primary_key=True
    )
    
    user_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    user_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    role_id: Mapped[int] = mapped_column(
       ForeignKey("roles.role_id"),
       nullable=False 
    )
    
    is_super_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false")
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
    
    role: Mapped["Role"] = relationship(
        back_populates="users"
    )
    
    user_permissions: Mapped[list["UserPermission"]] = relationship(
        back_populates="user"
    )