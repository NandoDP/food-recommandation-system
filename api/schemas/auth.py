from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str

class UserRegister(BaseModel):
    # email: EmailStr
    # password: str
    id: str
    last_name: str
    first_name: str 
    birth_date: Optional[str] = None 
    gender: Optional[str] = None
    weight: Optional[int] = None 
    height: Optional[int] = None
    registration_date: Optional[str] = None
    language: Optional[str] = "fr"

class UserResponse(BaseModel):
    id: int
    # username: str
    # email: str
    last_name: str
    first_name: str
    birth_date: Optional[datetime] = None
    gender: str
    weight: Optional[int] = None
    height: Optional[int] = None
    registration_date: datetime
    language: str
    
    class Config:
        from_attributes = True
