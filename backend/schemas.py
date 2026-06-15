from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    picture: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    picture: Optional[str] = None
    created_at: datetime


class ProblemDetails(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    status: Optional[int] = None
    detail: Optional[str] = None
    instance: Optional[str] = None
