"""Authentication routes.

Endpoints
---------
POST /api/v1/auth/register  — create an account, receive token pair
POST /api/v1/auth/login     — authenticate, receive token pair
POST /api/v1/auth/refresh   — exchange a refresh token for a new pair
GET  /api/v1/auth/me        — return the caller's profile
"""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
_limiter = Limiter(key_func=get_remote_address)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    PublicRegisterRequest,
    RefreshRequest,
    RegistrationResponse,
    ResendVerificationRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    VerificationResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserRead
from app.core.token_deny_list import add_to_deny_list
from app.security import create_access_token, create_refresh_token, decode_token
from app.services.auth_service import (
    AuthError,
    authenticate_user,
    get_user_by_email,
    get_user_by_id,
    public_register_user,
    register_user,
    resend_verification_code,
    verify_email_code,
)

from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _authenticate_and_issue_tokens(
    db: AsyncSession, email: str, password: str
) -> TokenResponse:
    """Validate credentials and return an access + refresh token pair.

    Shared by the JSON login endpoint and the OAuth2 form-based login
    endpoint so both produce identical tokens for the same credentials.
    """
    try:
        user = await authenticate_user(db, email, password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Create a new user and return an access + refresh token pair.

    - Validates password strength (min 8 chars, 1 uppercase, 1 digit).
    - Returns **409** if the email is already registered.
    """
    try:
        user = await register_user(db, data)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive tokens",
)
@_limiter.limit(f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute")
async def login(
    request: Request,
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Validate credentials and return an access + refresh token pair.

    Returns **401** on invalid credentials (email and password errors are
    intentionally indistinguishable to prevent user enumeration).
    """
    return await _authenticate_and_issue_tokens(db, data.email, data.password)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 password-flow login (used by Swagger UI's Authorize dialog)",
)
@_limiter.limit(f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute")
async def login_oauth2(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """OAuth2-compatible token endpoint for Swagger UI's "Authorize" dialog.

    Swagger sends `username`/`password` as form fields; `username` is
    treated as the user's email address. Returns the same token pair as
    `POST /auth/login`.
    """
    return await _authenticate_and_issue_tokens(db, form_data.username, form_data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an access token",
)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair.

    Both tokens are rotated on each refresh (refresh token rotation).
    Returns **401** if the refresh token is expired, malformed, or of the
    wrong type.
    """
    try:
        claims = decode_token(data.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(db, claims["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or has been disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current access token",
)
async def logout(
    token: str = Depends(_oauth2_scheme),
    current_user: User = Depends(get_current_user),
) -> None:
    """Add the current access token's JTI to the Redis deny-list.

    The token is invalidated immediately; subsequent requests with the same
    token receive HTTP 401. The deny-list entry expires when the token would
    have expired naturally — no unbounded Redis growth.
    """
    try:
        claims = decode_token(token, expected_type="access")
    except ValueError:
        return  # already invalid — nothing to revoke

    jti = claims.get("jti")
    exp = claims.get("exp")
    if jti and exp:
        await add_to_deny_list(jti, exp)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the current user's profile",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the authenticated caller.

    Requires a valid ``Authorization: Bearer <access_token>`` header.
    """
    return current_user


# ---------------------------------------------------------------------------
# Public registration flow
# ---------------------------------------------------------------------------


@router.post(
    "/public-register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Public self-registration — no authentication required",
)
async def public_register(
    data: PublicRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegistrationResponse:
    """Register a new user via the public sign-up form.

    - Account starts as unverified and pending admin approval.
    - A 6-digit verification code is sent to the email (or logged in console mode).
    - Login is blocked until email is verified AND admin approves the account.
    - Raises 409 if email already registered.
    - Raises 403 if REGISTRATION_OPEN=false.
    """
    if not getattr(settings, "REGISTRATION_OPEN", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is currently closed. Contact your administrator.",
        )

    try:
        user = await public_register_user(db, data)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    from app.services.email_service import send_verification_email
    send_verification_email(user.email, user.full_name, user.verification_code or "")

    auto_approve = getattr(settings, "REGISTRATION_AUTO_APPROVE", False)
    return RegistrationResponse(
        message=(
            "Registration successful. Please check your email for the verification code."
            if not auto_approve
            else "Registration successful. Check your email for the verification code. You will be activated after verification."
        ),
        email=user.email,
        requires_verification=True,
        requires_approval=not auto_approve,
    )


@router.post(
    "/verify-email",
    response_model=VerificationResponse,
    summary="Verify email address with the code sent during registration",
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> VerificationResponse:
    """Submit the 6-digit code from the verification email.

    - Marks the account as email-verified.
    - If REGISTRATION_AUTO_APPROVE=true, also activates the account immediately.
    - Raises 401 on invalid/expired code.
    """
    try:
        user = await verify_email_code(db, data.email, data.code)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    message = "Email verified successfully."
    if user.is_active:
        message += " Your account is now active. You can sign in."
    else:
        message += " Your account is pending administrator approval. You will be notified when approved."

    return VerificationResponse(
        message=message,
        email=user.email,
        is_active=user.is_active,
        approval_status=user.approval_status,
    )


@router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
    summary="Resend the email verification code",
)
async def resend_verification(
    data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate a new verification code and re-send the email.

    Returns 200 even if the email is not found (prevents user enumeration).
    """
    try:
        user = await resend_verification_code(db, data.email)
        from app.services.email_service import send_verification_email
        send_verification_email(user.email, user.full_name, user.verification_code or "")
    except AuthError:
        pass  # Silent — don't reveal whether email exists
    return {"message": "If this email is registered and unverified, a new code has been sent."}


# ---------------------------------------------------------------------------
# Activation (post-approval password creation)
# ---------------------------------------------------------------------------


class ActivateRequest(BaseModel):
    token: str
    new_password: str


class ValidateTokenRequest(BaseModel):
    token: str


@router.get(
    "/activate/validate",
    status_code=status.HTTP_200_OK,
    summary="Check activation token validity without consuming it",
)
async def validate_activation(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return 200 with full_name if the token is valid; 400 otherwise."""
    import logging as _logging
    from app.services.activation_service import validate_activation_token, ActivationError
    try:
        user = await validate_activation_token(db, token)
        return {"valid": True, "full_name": user.full_name, "email": user.email}
    except ActivationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        _logging.getLogger(__name__).exception("validate_activation unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(exc).__name__}: {exc}",
        )


@router.post(
    "/activate",
    status_code=status.HTTP_200_OK,
    summary="Consume an activation token and set a password",
)
async def activate_account(
    data: ActivateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Validate the one-time activation token, set the user's password, and activate the account."""
    from app.services.activation_service import consume_activation_token, ActivationError
    try:
        user = await consume_activation_token(db, data.token, data.new_password)
        return {"message": "Account activated. You may now sign in.", "email": user.email}
    except ActivationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


class ResendActivationRequest(BaseModel):
    email: str


@router.post(
    "/activate/resend",
    status_code=status.HTTP_200_OK,
    summary="Request a new activation link (for expired links)",
)
async def resend_activation(
    data: ResendActivationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Issue a new activation link for an approved-but-inactive user.

    Always returns 200 regardless of whether the email exists (prevents enumeration).
    """
    from app.services.activation_service import resend_activation_token, ActivationError
    from app.services.email_service import send_activation_email
    try:
        user = await get_user_by_email(db, data.email)
        if user and user.approval_status == "approved" and not user.is_active:
            raw_token = await resend_activation_token(db, user.id)
            send_activation_email(user.email, user.full_name, raw_token)
    except (ActivationError, Exception):
        pass  # Silent — prevents enumeration
    return {"message": "If your email is registered and pending activation, a new link has been sent."}
