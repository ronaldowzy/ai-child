from collections.abc import Callable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import AuthSessionRecord, Child, ChildAccountRecord
from app.db.session import SessionLocal
from app.domain.schemas.auth import AuthAccountRecordData, AuthSessionRecordData


class AuthRepositoryUnavailable(RuntimeError):
    pass


class AuthUsernameAlreadyExists(RuntimeError):
    pass


class AuthRepository:
    """DB-backed child-account auth repository.

    Only password hashes and token hashes are persisted; raw passwords and raw
    bearer tokens stay inside the service call path.
    """

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def create_account(
        self,
        *,
        account: AuthAccountRecordData,
        child_nickname: str,
    ) -> AuthAccountRecordData:
        try:
            with self._session_factory() as session:
                if session.get(Child, account.child_id) is None:
                    session.add(
                        Child(
                            id=account.child_id,
                            nickname=child_nickname or account.child_id,
                            timezone="Asia/Shanghai",
                            profile={},
                        )
                    )
                record = ChildAccountRecord(
                    id=account.id,
                    child_id=account.child_id,
                    username=account.username,
                    password_hash=account.password_hash,
                    created_by_guardian=account.created_by_guardian,
                    last_login_at=account.last_login_at,
                )
                session.add(record)
                session.commit()
                session.refresh(record)
                return self._to_account_data(record)
        except IntegrityError as exc:
            raise AuthUsernameAlreadyExists(account.username) from exc
        except SQLAlchemyError as exc:
            raise AuthRepositoryUnavailable(str(exc)) from exc

    def get_account_by_username(
        self,
        username: str,
    ) -> AuthAccountRecordData | None:
        try:
            with self._session_factory() as session:
                record = session.execute(
                    select(ChildAccountRecord).where(
                        ChildAccountRecord.username == username
                    )
                ).scalar_one_or_none()
                return self._to_account_data(record) if record else None
        except SQLAlchemyError as exc:
            raise AuthRepositoryUnavailable(str(exc)) from exc

    def get_account_by_id(self, account_id: str) -> AuthAccountRecordData | None:
        try:
            with self._session_factory() as session:
                record = session.get(ChildAccountRecord, account_id)
                return self._to_account_data(record) if record else None
        except SQLAlchemyError as exc:
            raise AuthRepositoryUnavailable(str(exc)) from exc

    def create_session(
        self,
        session_data: AuthSessionRecordData,
    ) -> AuthSessionRecordData:
        try:
            with self._session_factory() as session:
                record = AuthSessionRecord(
                    id=session_data.id,
                    child_account_id=session_data.child_account_id,
                    token_hash=session_data.token_hash,
                    created_at=session_data.created_at,
                    expires_at=session_data.expires_at,
                    revoked_at=session_data.revoked_at,
                )
                session.add(record)
                account = session.get(ChildAccountRecord, session_data.child_account_id)
                if account is not None:
                    account.last_login_at = session_data.created_at
                session.commit()
                session.refresh(record)
                return self._to_session_data(record)
        except SQLAlchemyError as exc:
            raise AuthRepositoryUnavailable(str(exc)) from exc

    def get_session_by_token_hash(
        self,
        token_hash: str,
    ) -> AuthSessionRecordData | None:
        try:
            with self._session_factory() as session:
                record = session.execute(
                    select(AuthSessionRecord).where(
                        AuthSessionRecord.token_hash == token_hash
                    )
                ).scalar_one_or_none()
                return self._to_session_data(record) if record else None
        except SQLAlchemyError as exc:
            raise AuthRepositoryUnavailable(str(exc)) from exc

    def revoke_session(self, token_hash: str, *, revoked_at: datetime) -> bool:
        try:
            with self._session_factory() as session:
                record = session.execute(
                    select(AuthSessionRecord).where(
                        AuthSessionRecord.token_hash == token_hash
                    )
                ).scalar_one_or_none()
                if record is None:
                    return False
                record.revoked_at = revoked_at
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise AuthRepositoryUnavailable(str(exc)) from exc

    def _to_account_data(
        self,
        record: ChildAccountRecord,
    ) -> AuthAccountRecordData:
        return AuthAccountRecordData(
            id=record.id,
            child_id=record.child_id,
            username=record.username,
            password_hash=record.password_hash,
            created_by_guardian=record.created_by_guardian,
            last_login_at=record.last_login_at,
        )

    def _to_session_data(
        self,
        record: AuthSessionRecord,
    ) -> AuthSessionRecordData:
        return AuthSessionRecordData(
            id=record.id,
            child_account_id=record.child_account_id,
            token_hash=record.token_hash,
            created_at=record.created_at,
            expires_at=record.expires_at,
            revoked_at=record.revoked_at,
        )


class InMemoryAuthRepository:
    """Fallback repository for local tests when PostgreSQL is unavailable."""

    def __init__(self) -> None:
        self.accounts_by_username: dict[str, AuthAccountRecordData] = {}
        self.accounts_by_id: dict[str, AuthAccountRecordData] = {}
        self.sessions_by_hash: dict[str, AuthSessionRecordData] = {}

    def create_account(
        self,
        *,
        account: AuthAccountRecordData,
        child_nickname: str,
    ) -> AuthAccountRecordData:
        if account.username in self.accounts_by_username:
            raise AuthUsernameAlreadyExists(account.username)
        self.accounts_by_username[account.username] = account
        self.accounts_by_id[account.id] = account
        return account

    def get_account_by_username(
        self,
        username: str,
    ) -> AuthAccountRecordData | None:
        return self.accounts_by_username.get(username)

    def get_account_by_id(self, account_id: str) -> AuthAccountRecordData | None:
        return self.accounts_by_id.get(account_id)

    def create_session(
        self,
        session_data: AuthSessionRecordData,
    ) -> AuthSessionRecordData:
        self.sessions_by_hash[session_data.token_hash] = session_data
        account = self.accounts_by_id.get(session_data.child_account_id)
        if account is not None:
            updated = account.model_copy(update={"last_login_at": session_data.created_at})
            self.accounts_by_id[updated.id] = updated
            self.accounts_by_username[updated.username] = updated
        return session_data

    def get_session_by_token_hash(
        self,
        token_hash: str,
    ) -> AuthSessionRecordData | None:
        return self.sessions_by_hash.get(token_hash)

    def revoke_session(self, token_hash: str, *, revoked_at: datetime) -> bool:
        session = self.sessions_by_hash.get(token_hash)
        if session is None:
            return False
        self.sessions_by_hash[token_hash] = session.model_copy(
            update={"revoked_at": revoked_at}
        )
        return True
