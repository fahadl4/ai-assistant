from pydantic import BaseModel, Field

class UserBase(BaseModel):
    user_name: str
    user_email: str

class UserRegistration(UserBase):
    password: str
    role_id: int = Field(gt=0)

class UserLogin(BaseModel):
    user_email: str
    password: str

class UserResponse(UserBase):
    user_id: int
    role_id: int
    
    model_config = {
        "from_attributes": True
    }
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class InitialAdminSetup(UserBase):
    password: str
    setup_secret: str