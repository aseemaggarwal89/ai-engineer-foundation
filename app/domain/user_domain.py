from pydantic import BaseModel
from app.db.models.user import User
from app.domain.role import Role


class UserRegisterRequest(BaseModel):
    id: str
    role: Role
    
    def to_model(self) -> User:
        return User(
            id=self.id,
            is_active=True,
            role=self.role or Role.USER,
        )


class UserReadResponse(BaseModel):
    id: str
    is_active: bool
    role: Role

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserReadResponse]
