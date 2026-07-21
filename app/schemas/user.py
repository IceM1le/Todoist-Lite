from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserLogin(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=3, max_length=72)


class UserCreate(UserLogin):
    email: str = Field(..., max_length=255)
    telegram_chat_id: str = Field(None, max_length=100)

class UserResponse(BaseModel):
    name: str
    email: str
    telegram_chat_id: Optional[str] = Field(None)

class UserUpdate(BaseModel):
    telegram_chat_id: str = Field(None, max_length=100)