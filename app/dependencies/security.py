from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Request, status
from app.domain.exceptions import AuthenticationError

from app.security.jwt import decode_token

_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="JWT"
)


# async def security(request: Request) -> HTTPAuthorizationCredentials:
#     creds = await _bearer(request)

#     if not creds:
#         raise AuthenticationError("Missing authentication token")
    
#     return creds


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    if not credentials:
        raise AuthenticationError("Missing authentication token")

    return decode_token(credentials.credentials)