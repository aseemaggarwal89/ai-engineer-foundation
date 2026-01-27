from typing import List
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.domain.entities.user import User


class UserRegisterRequest(BaseModel):
    """
    Public user registration request.

    Client provides:
    - email
    - password

    Server controls:
    - id
    - role
    - is_active
    """

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Password must be between 8 and 72 characters",
    )


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    role: str

    @staticmethod
    def from_domain(user: User) -> "UserResponse":
        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            role=user.role.value,
        )


class UserListResponse(BaseModel):
    users: list[UserResponse]

    @staticmethod
    def from_domain(users: List[User]) -> "UserListResponse":
        return UserListResponse(
            users=[UserResponse.from_domain(user) for user in users]
        )
