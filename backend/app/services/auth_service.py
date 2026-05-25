from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import secrets
from uuid import uuid4

from app.core.config import get_settings
from app.domain.schemas.auth import (
    AuthAccountProfile,
    AuthAccountRecordData,
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthSessionRecordData,
    AuthSessionResponse,
    profile_preferences_from_input,
)
from app.domain.schemas.parent_policy import ParentPolicyUpdateRequest
from app.repositories.auth_repository import (
    AuthRepository,
    AuthRepositoryUnavailable,
    AuthUsernameAlreadyExists,
    InMemoryAuthRepository,
)
from app.services.parent_policy_service import (
    ParentPolicyService,
    get_parent_policy_service,
)


class AuthServiceError(RuntimeError):
    pass


class AuthInvalidCredentials(AuthServiceError):
    pass


class AuthTokenInvalid(AuthServiceError):
    pass


class AuthTokenExpired(AuthServiceError):
    pass


class AuthAccountExists(AuthServiceError):
    pass


class AuthStorageUnavailable(AuthServiceError):
    pass


class AuthService:
    PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
    PASSWORD_HASH_ITERATIONS = 210_000
    SESSION_TTL_DAYS = 30

    def __init__(
        self,
        *,
        repository: AuthRepository | InMemoryAuthRepository | None = None,
        fallback_repository: InMemoryAuthRepository | None = None,
        parent_policy_service: ParentPolicyService | None = None,
        fallback_to_memory: bool | None = None,
    ) -> None:
        self._repository = repository or AuthRepository()
        self._fallback_repository = fallback_repository or InMemoryAuthRepository()
        self._using_fallback = isinstance(self._repository, InMemoryAuthRepository)
        self._fallback_to_memory = (
            get_settings().allow_auth_memory_fallback
            if fallback_to_memory is None
            else fallback_to_memory
        )
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )

    def register(self, request: AuthRegisterRequest) -> AuthSessionResponse:
        username = self._normalize_username(request.username)
        now = self._now()
        child_id = f"child_{uuid4().hex[:16]}"
        account = AuthAccountRecordData(
            id=f"acct_{uuid4().hex}",
            child_id=child_id,
            username=username,
            password_hash=self.hash_password(request.password),
            created_by_guardian=True,
            last_login_at=None,
        )
        try:
            saved = self._repo().create_account(
                account=account,
                child_nickname=(request.child_nickname or "").strip(),
            )
        except AuthUsernameAlreadyExists as exc:
            raise AuthAccountExists("username already exists") from exc
        except AuthRepositoryUnavailable:
            if not self._fallback_to_memory:
                raise AuthStorageUnavailable("auth storage unavailable")
            self._using_fallback = True
            try:
                saved = self._repo().create_account(
                    account=account,
                    child_nickname=(request.child_nickname or "").strip(),
                )
            except AuthUsernameAlreadyExists as exc:
                raise AuthAccountExists("username already exists") from exc

        self._upsert_parent_policy_from_registration(saved.child_id, request)
        return self._create_session_response(saved, now=now)

    def login(self, request: AuthLoginRequest) -> AuthSessionResponse:
        username = self._normalize_username(request.username)
        account = self._get_account_by_username(username)
        if account is None or not self.verify_password(
            request.password,
            account.password_hash,
        ):
            raise AuthInvalidCredentials("invalid username or password")
        return self._create_session_response(account, now=self._now())

    def account_for_token(self, token: str) -> AuthAccountProfile:
        session = self._session_for_token(token)
        now = self._now()
        if session.revoked_at is not None:
            raise AuthTokenInvalid("session revoked")
        if self._aware(session.expires_at) <= now:
            raise AuthTokenExpired("session expired")
        account = self._repo().get_account_by_id(session.child_account_id)
        if account is None:
            raise AuthTokenInvalid("account not found")
        return self._account_profile(account)

    def logout(self, token: str) -> bool:
        token_hash = self.hash_token(token)
        try:
            return self._repo().revoke_session(token_hash, revoked_at=self._now())
        except AuthRepositoryUnavailable:
            if not self._fallback_to_memory:
                raise AuthStorageUnavailable("auth storage unavailable")
            self._using_fallback = True
            return self._repo().revoke_session(token_hash, revoked_at=self._now())

    def hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.PASSWORD_HASH_ITERATIONS,
        )
        return "$".join(
            [
                self.PASSWORD_HASH_ALGORITHM,
                str(self.PASSWORD_HASH_ITERATIONS),
                base64.b64encode(salt).decode("ascii"),
                base64.b64encode(digest).decode("ascii"),
            ]
        )

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, digest_text = password_hash.split(
                "$",
                3,
            )
            if algorithm != self.PASSWORD_HASH_ALGORITHM:
                return False
            salt = base64.b64decode(salt_text.encode("ascii"))
            expected = base64.b64decode(digest_text.encode("ascii"))
            iterations = int(iterations_text)
        except Exception:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected)

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _create_session_response(
        self,
        account: AuthAccountRecordData,
        *,
        now: datetime,
    ) -> AuthSessionResponse:
        raw_token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(days=self.SESSION_TTL_DAYS)
        session_data = AuthSessionRecordData(
            id=f"sess_{uuid4().hex}",
            child_account_id=account.id,
            token_hash=self.hash_token(raw_token),
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
        )
        try:
            self._repo().create_session(session_data)
        except AuthRepositoryUnavailable:
            if not self._fallback_to_memory:
                raise AuthStorageUnavailable("auth storage unavailable")
            self._using_fallback = True
            self._repo().create_session(session_data)
        refreshed = self._repo().get_account_by_id(account.id) or account
        return AuthSessionResponse(
            token=raw_token,
            expires_at=expires_at,
            account=self._account_profile(refreshed),
        )

    def _session_for_token(self, token: str) -> AuthSessionRecordData:
        token_hash = self.hash_token(token)
        try:
            session = self._repo().get_session_by_token_hash(token_hash)
        except AuthRepositoryUnavailable:
            if not self._fallback_to_memory:
                raise AuthStorageUnavailable("auth storage unavailable")
            self._using_fallback = True
            session = self._repo().get_session_by_token_hash(token_hash)
        if session is None:
            raise AuthTokenInvalid("session not found")
        return session

    def _get_account_by_username(
        self,
        username: str,
    ) -> AuthAccountRecordData | None:
        try:
            return self._repo().get_account_by_username(username)
        except AuthRepositoryUnavailable:
            if not self._fallback_to_memory:
                raise AuthStorageUnavailable("auth storage unavailable")
            self._using_fallback = True
            return self._repo().get_account_by_username(username)

    def _account_profile(self, account: AuthAccountRecordData) -> AuthAccountProfile:
        policy = self._parent_policy_service.get_policy(account.child_id)
        preferences = policy.communication_preferences
        return AuthAccountProfile(
            child_account_id=account.id,
            child_id=account.child_id,
            username=account.username,
            created_by_guardian=account.created_by_guardian,
            child_nickname=policy.child_nickname,
            child_display_name=policy.child_display_name,
            child_age=self._optional_int(preferences.get("child_age")),
            child_grade=self._optional_str(preferences.get("child_grade")),
            child_call_preference=self._optional_str(
                preferences.get("child_call_preference")
            ),
            child_interests=self._string_list(preferences.get("child_interests")),
            topic_boundaries=self._string_list(preferences.get("topic_boundaries")),
            last_login_at=account.last_login_at,
        )

    def _upsert_parent_policy_from_registration(
        self,
        child_id: str,
        request: AuthRegisterRequest,
    ) -> None:
        current = self._parent_policy_service.get_policy(child_id)
        self._parent_policy_service.update_policy(
            ParentPolicyUpdateRequest(
                child_id=child_id,
                child_nickname=request.child_nickname,
                child_display_name=request.child_display_name,
                communication_preferences=profile_preferences_from_input(
                    request,
                    current.communication_preferences,
                ),
            )
        )

    def _repo(self) -> AuthRepository | InMemoryAuthRepository:
        return self._fallback_repository if self._using_fallback else self._repository

    def _normalize_username(self, username: str) -> str:
        return username.strip().lower()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _aware(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def _optional_int(self, value: object) -> int | None:
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _optional_str(self, value: object) -> str | None:
        text = str(value or "").strip()
        return text or None

    def _string_list(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split("，") if item.strip()]
        return []


_auth_service = AuthService()


def get_auth_service() -> AuthService:
    return _auth_service
