from pydantic import BaseModel, Field, field_validator


class UserLogin(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=3, max_length=72)


class UserCreate(UserLogin):
    email: str = Field(..., max_length=255)

class UserResponse(BaseModel):
    name: str
    email: str