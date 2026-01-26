from passlib.context import CryptContext

# Central password hashing context
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plaintext password.
    """
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against its hash.
    """
    return _pwd_context.verify(password, password_hash)
