from pydantic import BaseModel, EmailStr, Field
import uuid

class UserRegisteration(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    full_name: str = Field(min_length=3, max_length=255)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str

    class Config:
        orm_mode = True