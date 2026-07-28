from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.domain.entities.user import User
from app.domain.entities.user_role import UserRole
from app.domain.exceptions.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)
from app.domain.use_cases.user.login_user import LoginUserUseCase
from app.domain.use_cases.user.register_user import RegisterUserUseCase
from app.security.dependencies import get_current_user
from app.security.jwt import create_access_token, decode_token, settings
from app.security.password import hash_password, verify_password
from app.security.security import get_token_payload


class FakeUserRepository:
    def __init__(self, user: User | None = None):
        self.user = user
        self.created_password_hash = None
        self.lookup_emails = []

    async def get_by_email(self, email: str) -> User | None:
        self.lookup_emails.append(email)
        if self.user and self.user.email == email:
            return self.user
        return None

    async def create(self, user: User, password_hash: str) -> User:
        self.user = User(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            role=user.role,
            password_hash=password_hash,
        )
        self.created_password_hash = password_hash
        return self.user


class FakeCurrentUserUseCase:
    def __init__(self, user: User):
        self.user = user
        self.user_id = None

    async def execute(self, user_id):
        self.user_id = user_id
        return self.user


def make_user(
    *,
    email: str = "user@example.com",
    role: UserRole = UserRole.USER,
    is_active: bool = True,
    password: str = "correct-password",
) -> User:
    return User(
        id=uuid4(),
        email=email,
        is_active=is_active,
        role=role,
        password_hash=hash_password(password),
    )


def test_passwords_are_hashed_and_verified_without_storing_plaintext():
    password_hash = hash_password("correct-password")

    assert password_hash != "correct-password"
    assert verify_password("correct-password", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


@pytest.mark.asyncio
async def test_registration_normalizes_email_and_hashes_password():
    repo = FakeUserRepository()
    use_case = RegisterUserUseCase(repo)

    user = await use_case.execute(
        email="  USER@Example.COM  ",
        password="correct-password",
    )

    assert user.email == "user@example.com"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert repo.lookup_emails == ["user@example.com"]
    assert repo.created_password_hash != "correct-password"
    assert verify_password("correct-password", repo.created_password_hash) is True


@pytest.mark.asyncio
async def test_registration_rejects_duplicate_normalized_email():
    repo = FakeUserRepository(user=make_user(email="user@example.com"))
    use_case = RegisterUserUseCase(repo)

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            email="USER@Example.COM",
            password="correct-password",
        )


@pytest.mark.asyncio
async def test_login_normalizes_email_and_returns_access_token():
    repo = FakeUserRepository(user=make_user(email="user@example.com"))
    use_case = LoginUserUseCase(repo)

    result = await use_case.execute(
        email=" USER@Example.COM ",
        password="correct-password",
    )

    assert result.user.email == "user@example.com"
    assert repo.lookup_emails == ["user@example.com"]
    assert decode_token(result.access_token)["sub"] == str(result.user.id)


@pytest.mark.asyncio
async def test_login_uses_common_error_for_unknown_email_and_wrong_password():
    unknown_email_use_case = LoginUserUseCase(FakeUserRepository())
    wrong_password_use_case = LoginUserUseCase(
        FakeUserRepository(user=make_user(email="user@example.com"))
    )

    with pytest.raises(AuthenticationError) as unknown_exc:
        await unknown_email_use_case.execute("missing@example.com", "password")

    with pytest.raises(AuthenticationError) as wrong_password_exc:
        await wrong_password_use_case.execute("user@example.com", "wrong")

    assert str(unknown_exc.value) == "Invalid email or password"
    assert str(wrong_password_exc.value) == "Invalid email or password"


def test_jwt_contains_verified_claims_and_decodes_successfully():
    user = make_user(role=UserRole.ADMIN)

    token = create_access_token(user)
    payload = decode_token(token)

    assert payload["sub"] == str(user.id)
    assert payload["role"] == UserRole.ADMIN.value
    assert payload["exp"] > int(datetime.now(timezone.utc).timestamp())


@pytest.mark.asyncio
async def test_bearer_token_payload_rejects_missing_token():
    with pytest.raises(AuthenticationError):
        await get_token_payload(credentials=None)


@pytest.mark.asyncio
async def test_bearer_token_payload_rejects_malformed_token():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="not-a-jwt",
    )

    with pytest.raises(AuthenticationError):
        await get_token_payload(credentials=credentials)


def test_jwt_rejects_expired_token():
    expired_payload = {
        "sub": str(uuid4()),
        "role": UserRole.USER.value,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(AuthenticationError):
        decode_token(token)


def test_jwt_rejects_unsupported_algorithm():
    payload = {
        "sub": str(uuid4()),
        "role": UserRole.USER.value,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS512")

    with pytest.raises(AuthenticationError):
        decode_token(token)


@pytest.mark.asyncio
async def test_current_user_resolution_uses_database_user_not_role_claim_only():
    database_user = make_user(role=UserRole.USER)
    current_user_use_case = FakeCurrentUserUseCase(database_user)

    user = await get_current_user(
        payload={"sub": str(database_user.id), "role": UserRole.ADMIN.value},
        current_user_use_case=current_user_use_case,
    )

    assert user.role == UserRole.USER
    assert current_user_use_case.user_id == str(database_user.id)


@pytest.mark.asyncio
async def test_current_user_rejects_missing_subject_claim():
    with pytest.raises(AuthenticationError):
        await get_current_user(
            payload={"role": UserRole.USER.value},
            current_user_use_case=FakeCurrentUserUseCase(make_user()),
        )
