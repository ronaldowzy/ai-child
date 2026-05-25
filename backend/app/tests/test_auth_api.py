from fastapi.testclient import TestClient
from uuid import uuid4

from app.services.auth_service import AuthService

from app.main import app


client = TestClient(app)


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
