from fastapi import APIRouter, Header, HTTPException, status

from app.domain.schemas.auth import (
    AuthAccountProfile,
    AuthLoginRequest,
    AuthLogoutResponse,
    AuthMeResponse,
    AuthRegisterRequest,
    AuthSessionResponse,
)
from app.services.auth_service import (
    AuthAccountExists,
    AuthInvalidCredentials,
    AuthService,
    AuthServiceError,
    AuthStorageUnavailable,
    AuthTokenInvalid,
    get_auth_service,
)


router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = get_auth_service()


@router.post(
    "/register",
    response_model=AuthSessionResponse,
    response_model_exclude_none=True,
)
def register_child_account(request: AuthRegisterRequest) -> AuthSessionResponse:
    try:
        return auth_service.register(request)
    except AuthAccountExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already exists",
        ) from exc
    except AuthStorageUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth storage unavailable",
        ) from exc


@router.post(
    "/login",
    response_model=AuthSessionResponse,
    response_model_exclude_none=True,
)
def login_child_account(request: AuthLoginRequest) -> AuthSessionResponse:
    try:
        return auth_service.login(request)
    except AuthInvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        ) from exc
    except AuthStorageUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth storage unavailable",
        ) from exc


@router.get(
    "/me",
    response_model=AuthMeResponse,
    response_model_exclude_none=True,
)
def get_current_account(
    authorization: str | None = Header(default=None),
) -> AuthMeResponse:
    return AuthMeResponse(
        account=required_auth_account(
            authorization,
            service=auth_service,
        )
    )


@router.post("/logout", response_model=AuthLogoutResponse)
def logout_current_account(
    authorization: str | None = Header(default=None),
) -> AuthLogoutResponse:
    token = required_bearer_token(authorization)
    auth_service.logout(token)
    return AuthLogoutResponse(revoked=True)


def optional_auth_account(
    authorization: str | None,
    *,
    service: AuthService | None = None,
) -> AuthAccountProfile | None:
    token = bearer_token(authorization)
    if token is None:
        return None
    try:
        return (service or auth_service).account_for_token(token)
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired session",
        ) from exc


def required_auth_account(
    authorization: str | None,
    *,
    service: AuthService | None = None,
) -> AuthAccountProfile:
    token = required_bearer_token(authorization)
    try:
        return (service or auth_service).account_for_token(token)
    except (AuthServiceError, AuthTokenInvalid) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired session",
        ) from exc


def required_bearer_token(authorization: str | None) -> str:
    token = bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )
    return token


def bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
