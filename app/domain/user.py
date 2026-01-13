from pydantic import BaseModel
from app.models.user import User


class UserRegisterRequest(BaseModel):
    id: str
    
    def to_model(self) -> User:
        return User(
            id=self.id,
            is_active=True
        )


class UserReadResponse(BaseModel):
    id: str
    is_active: bool

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserReadResponse]
