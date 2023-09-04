from typing import Optional

from fastapi import Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi.logger import logger
from jose import JWTError, jwt
from pydantic import ValidationError

from sedbackend.apps.core.authentication.login import get_user_with_pwd_from_db, SECRET_KEY, ALGORITHM, pwd_context, \
    parse_scopes_array
from sedbackend.apps.core.authentication.models import TokenData
from sedbackend.apps.core.users.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/core/auth/token",
)


async def verify_scopes(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    if security_scopes.scopes is None or len(security_scopes.scopes) == 0:
        return

    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": authenticate_value}
    )

    try:
        # The payload is a dict. It contains "sub" which is the username, "scopes", which is a list of scopes,
        # and "exp" which is a timestamp representing the time when the token expires.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # dict contains 'sub', wh
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception

    logger.debug(f"VERIFY SCOPE: Required scopes: {security_scopes.scopes}, user scopes: {token_data.scopes}")

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            logger.warning(f'VERIFY SCOPE: User "{token_data.username}" attempted to access an endpoint without the appropriate scope.')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
                headers={"WWW-Authenticate": authenticate_value}
            )

    return True


async def verify_token(security_scopes: SecurityScopes, request: Request, token: str = Depends(oauth2_scheme)):
    """
    Can be used as a dependency to check if a user is logged in.
    This is done by asserting that the session token exists and has not expired.
    :param security_scopes: Clearance/permissions
    :param token: The token
    :param request: HTTP Request
    :return: The user
    """

    client_host = request.client.host

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": authenticate_value}
    )

    try:
        token_data = parse_jwt_token(token)
    except JWTError:
        raise credentials_exception

    user = get_user_with_pwd_from_db(username=token_data.username)
    # Requested user does not exist
    if not user:
        raise credentials_exception

    # Assert that the user has the scopes it claims it has
    scopes_in_db = set(parse_scopes(user.scopes))
    for scope in token_data.scopes:
        if scope not in scopes_in_db:
            raise HTTPException(status_code=401, detail="Scope validation failed.")

    # Store user ID in request for easy access
    request.state.user_id = user.id
    return user


def parse_jwt_token(token) -> Optional[TokenData]:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
        raise JWTError
    token_scopes = payload.get("scopes", [])
    token_exp = payload.get("exp")

    token_data = TokenData(scopes=token_scopes, username=username, expires=token_exp)
    return token_data


async def get_current_active_user(current_user: User = Depends(verify_token)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_password_hash(plain_pwd):
    return pwd_context.hash(plain_pwd)


def parse_scopes(scopes_array: str):
    """
    Parses a scopes string into an array

    :param scopes_array: String array of scopes
    :return:
    """
    return parse_scopes_array(scopes_array)

