from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.config import get_settings
from app.domain.entities.user import User
from app.domain.exceptions.exceptions import AuthenticationError

# # flake8: noqa: E501

settings = get_settings()


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise AuthenticationError("Invalid or expired token")

    exp = payload.get("exp")
    if exp is None:
        raise AuthenticationError("Invalid token")

    if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(tz=timezone.utc):
        raise AuthenticationError("Token expired")

    return payload


def create_access_token(user: User) -> str:
    """
    Create a JWT access token.

    - subject: user identifier (stored in `sub`)
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )

    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )