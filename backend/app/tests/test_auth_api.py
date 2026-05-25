from datetime import date, datetime, timedelta, timezone
import json

from fastapi.testclient import TestClient
from uuid import uuid4

from app.api.v1 import conversation as conversation_api
from app.api.v1 import conversation_attachment as attachment_api
from app.api.v1 import conversation_opening as opening_api
from app.api.v1 import conversation_stream as stream_api
from app.api.v1 import parent_report as parent_report_api
from app.domain.attachment import (
    AttachmentCreateResponse,
    ImagePurpose,
    RecognizedContent,
)
from app.domain.parent_report import ParentReport, ParentReportGenerationStatus
from app.domain.schemas.auth import AuthLoginRequest, AuthRegisterRequest
from app.domain.schemas.conversation import (
    ConversationMessageResponse,
    Reply,
    SessionState,
)
from app.repositories.auth_repository import (
    AuthRepositoryUnavailable,
    InMemoryAuthRepository,
)
from app.services.auth_service import (
    AuthService,
    AuthStorageUnavailable,
    AuthTokenExpired,
    AuthTokenInvalid,
)

from app.main import app


client = TestClient(app)


def _register_test_session() -> tuple[str, str]:
    username = f"task10_auth_route_{uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "safe-password-09"},
    )
    assert response.status_code == 200
    body = response.json()
    return body["token"], body["account"]["child_id"]


def _conversation_response() -> ConversationMessageResponse:
    return ConversationMessageResponse(
        reply=Reply(text="小白狐知道了。"),
        ui_actions=[],
        session_state=SessionState(
            base_scene="conversation.open",
            active_scene="conversation.open",
        ),
    )


def _attachment_response() -> AttachmentCreateResponse:
    return AttachmentCreateResponse(
        attachment_id="att_task10_auth",
        recognized_content=RecognizedContent(
            type="image_observation",
            text="一张测试图片。",
            confidence=0.9,
            provider_name="test",
            image_purpose=ImagePurpose.SHARE,
        ),
        reply=Reply(text="我看到这张图片了。"),
        ui_actions=[],
        session_state=SessionState(
            base_scene="conversation.open",
            active_scene="conversation.open",
        ),
    )


def test_auth_service_hashes_password_and_token_without_plaintext() -> None:
    service = AuthService()
    password = "safe-password-09"
    token = "raw-token-value"

    password_hash = service.hash_password(password)
    token_hash = service.hash_token(token)

    assert password not in password_hash
    assert password_hash.startswith("pbkdf2_sha256$")
    assert service.verify_password(password, password_hash) is True
    assert token not in token_hash
    assert len(token_hash) == 64


def test_register_login_me_logout_flow_uses_hashes_and_bearer_session() -> None:
    username = f"task09_child_account_{uuid4().hex[:8]}"
    password = "safe-password-09"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": password,
            "child_nickname": "豆豆",
            "child_age": 8,
            "child_interests": ["恐龙", "画画"],
            "topic_boundaries": ["比赛成绩"],
        },
    )

    assert register_response.status_code == 200
    body = register_response.json()
    assert body["token"]
    assert body["token"] != password
    assert body["account"]["username"] == username
    assert body["account"]["child_id"].startswith("child_")
    assert body["account"]["child_nickname"] == "豆豆"
    assert body["account"]["child_interests"] == ["恐龙", "画画"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["account"]["child_id"] == body["account"]["child_id"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token"] != body["token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {body['token']}"},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["revoked"] is True

    revoked_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['token']}"},
    )
    assert revoked_me.status_code == 401


def test_login_rejects_invalid_credentials() -> None:
    username = f"task09_invalid_login_{uuid4().hex[:8]}"
    password = "safe-password-09"
    client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_auth_service_rejects_expired_and_revoked_sessions() -> None:
    repository = InMemoryAuthRepository()
    service = AuthService(repository=repository, fallback_repository=repository)
    session = service.register(
        request=AuthRegisterRequest(
            username=f"task10_expired_{uuid4().hex[:8]}",
            password="safe-password-09",
        )
    )

    token_hash = service.hash_token(session.token)
    stored = repository.sessions_by_hash[token_hash]
    repository.sessions_by_hash[token_hash] = stored.model_copy(
        update={"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}
    )

    try:
        service.account_for_token(session.token)
    except AuthTokenExpired:
        pass
    else:
        raise AssertionError("expired token should be rejected")

    fresh = service.login(
        request=AuthLoginRequest(
            username=session.account.username,
            password="safe-password-09",
        )
    )
    assert service.logout(fresh.token) is True
    try:
        service.account_for_token(fresh.token)
    except AuthTokenInvalid:
        pass
    else:
        raise AssertionError("revoked token should be rejected")


def test_auth_service_does_not_memory_fallback_when_disabled() -> None:
    class UnavailableRepository:
        def create_account(self, *, account, child_nickname):
            raise AuthRepositoryUnavailable("db unavailable")

        def get_account_by_username(self, username):
            raise AuthRepositoryUnavailable("db unavailable")

    service = AuthService(
        repository=UnavailableRepository(),
        fallback_to_memory=False,
    )

    try:
        service.register(
            request=AuthRegisterRequest(
                username=f"task10_no_memory_{uuid4().hex[:8]}",
                password="safe-password-09",
            )
        )
    except AuthStorageUnavailable:
        pass
    else:
        raise AssertionError("formal auth runtime must not fall back to memory")


def test_authenticated_parent_policy_defaults_to_account_child_id() -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": f"task09_policy_account_{uuid4().hex[:8]}",
            "password": "safe-password-09",
            "child_nickname": "小米",
        },
    )
    token = register_response.json()["token"]
    child_id = register_response.json()["account"]["child_id"]

    response = client.get(
        "/api/v1/parent/policy",
        params={"child_id": "wrong_dev_child"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["child_id"] == child_id
    assert response.json()["child_nickname"] == "小米"


def test_revoked_optional_auth_route_returns_401() -> None:
    token, _child_id = _register_test_session()
    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_response.status_code == 200

    response = client.post(
        "/api/v1/conversation/opening",
        json={
            "childId": "wrong_dev_child",
            "sessionId": "task10_revoked_session",
            "clientContext": {
                "deviceTime": "2026-05-21T16:35:00+08:00",
                "timezone": "Asia/Shanghai",
                "appMode": "child",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_authenticated_conversation_and_opening_override_client_child_id(
    monkeypatch,
) -> None:
    token, child_id = _register_test_session()

    class CapturingConversationService:
        child_id: str | None = None

        def handle_message(self, request):
            self.child_id = request.child_id
            return _conversation_response()

    class CapturingOpeningService:
        child_id: str | None = None

        def create_opening(self, request):
            self.child_id = request.child_id
            return _conversation_response()

    conversation_service = CapturingConversationService()
    opening_service = CapturingOpeningService()
    monkeypatch.setattr(conversation_api, "conversation_service", conversation_service)
    monkeypatch.setattr(opening_api, "get_opening_service", lambda: opening_service)

    message_response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": "wrong_dev_child",
            "session_id": "task10_auth_message_session",
            "input": {"type": "text", "text": "我想聊恐龙", "attachments": []},
            "client_context": {
                "device_time": "2026-05-21T16:35:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    opening_response = client.post(
        "/api/v1/conversation/opening",
        json={
            "childId": "wrong_dev_child",
            "sessionId": "task10_auth_opening_session",
            "clientContext": {
                "deviceTime": "2026-05-21T16:35:00+08:00",
                "timezone": "Asia/Shanghai",
                "appMode": "child",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert message_response.status_code == 200
    assert opening_response.status_code == 200
    assert conversation_service.child_id == child_id
    assert opening_service.child_id == child_id


def test_authenticated_stream_overrides_client_child_id(monkeypatch) -> None:
    token, child_id = _register_test_session()

    class CapturingStreamService:
        child_id: str | None = None

        def stream_ndjson(self, request):
            self.child_id = request.child_id
            yield json.dumps(
                {
                    "event_id": "evt_task10_auth",
                    "turn_id": "turn_task10_auth",
                    "seq": 1,
                    "type": "done",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {"status": "completed"},
                }
            ) + "\n"

    stream_service = CapturingStreamService()
    monkeypatch.setattr(stream_api, "conversation_stream_service", stream_service)

    response = client.post(
        "/api/v1/conversation/stream",
        json={
            "child_id": "wrong_dev_child",
            "session_id": "task10_auth_stream_session",
            "input": {"type": "text", "text": "我想聊恐龙", "attachments": []},
            "client_context": {
                "device_time": "2026-05-21T16:35:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
            "stream_options": {"include_tts": False},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert stream_service.child_id == child_id


def test_authenticated_parent_report_overrides_client_child_id(monkeypatch) -> None:
    token, child_id = _register_test_session()

    class CapturingParentReportService:
        child_id: str | None = None

        def get_daily_report(self, child_id_arg, report_date=None):
            self.child_id = child_id_arg
            return ParentReport(
                child_id=child_id_arg,
                date=report_date or date(2026, 5, 25),
                summary="家长摘要测试。",
                created_at=datetime.now(timezone.utc),
                generation_status=ParentReportGenerationStatus.DETERMINISTIC_FALLBACK,
                generated_by="test",
            )

    report_service = CapturingParentReportService()
    monkeypatch.setattr(parent_report_api, "parent_report_service", report_service)

    response = client.get(
        "/api/v1/parent/reports/wrong_dev_child",
        params={"date": "2026-05-25"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["child_id"] == child_id
    assert report_service.child_id == child_id


def test_authenticated_attachment_routes_override_client_child_id(monkeypatch) -> None:
    token, child_id = _register_test_session()

    class CapturingAttachmentService:
        create_child_id: str | None = None
        upload_child_id: str | None = None

        def create_attachment(self, request):
            self.create_child_id = request.child_id
            return _attachment_response()

        def create_real_image_upload(self, upload):
            self.upload_child_id = upload.child_id
            return _attachment_response()

    service = CapturingAttachmentService()
    monkeypatch.setattr(attachment_api, "attachment_service", service)

    create_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "wrong_dev_child",
            "session_id": "task10_auth_attachment_session",
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_photo",
            "mock_vision_text": "一张测试图片。",
            "mock_confidence": 0.9,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    upload_response = client.post(
        "/api/v1/attachments/images",
        data={
            "child_id": "wrong_dev_child",
            "session_id": "task10_auth_upload_session",
            "image_purpose": "share",
        },
        files={"file": ("sample.jpg", b"not-a-real-child-photo", "image/jpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert create_response.status_code == 200
    assert upload_response.status_code == 200
    assert service.create_child_id == child_id
    assert service.upload_child_id == child_id
