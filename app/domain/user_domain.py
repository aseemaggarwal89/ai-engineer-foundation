from pydantic import BaseModel, EmailStr, Field
from app.db.models.user import User
from app.domain.role import Role
import uuid

# class UserRegisterRequest(BaseModel):
#     id: str
#     role: Role
#     email: str
#     password: str = Field(
#         min_length=8,
#         max_length=72,
#         description="Password must be between 8 and 72 characters",
#     )

#     def to_model(self) -> User:
#         return User(
#             id=self.id,
#             is_active=True,
#             role=self.role or Role.USER,
#             email=self.email,
#         )


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

    def to_model(self) -> User:
        """
        Convert request DTO to User ORM model.
        """
        return User(
            id=str(uuid.uuid4()),
            email=self.email,
            role=Role.USER,       # default role
            is_active=True,
        )


class UserReadResponse(BaseModel):
    is_active: bool
    role: Role
    email: str

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserReadResponse]
