from uuid import UUID

from app.db.models.user_orm import UserORM
from app.domain.entities.user import User


def orm_to_domain_user(orm: UserORM) -> User:
    return User(
        id=UUID(orm.id),
        email=orm.email,
        is_active=orm.is_active,
        role=orm.role,
        password_hash=orm.password_hash,
    )


def domain_to_orm_user(domain: User) -> UserORM:
    return UserORM(
        id=str(domain.id),
        email=domain.email,
        is_active=domain.is_active,
        role=domain.role,
        password_hash=domain.password_hash,  # placeholder if needed
    )
