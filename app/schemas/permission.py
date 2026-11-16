from pydantic import BaseModel

class PermissionAssignment(BaseModel):
    permission_key: str
    is_enabled: bool

class UserPermissionsUpdate(BaseModel):
    permissions: list[PermissionAssignment]

class PermissionResponse(BaseModel):
    permission_key: str
    description: str
    is_enabled: bool