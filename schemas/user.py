from pydantic import BaseModel, EmailStr, Field

class UserRegisteration(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    full_name: str = Field(min_length=3, max_length=255)