from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import debug_house_object as debug_api
from app.core.config import get_settings
from app.main import app
from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository
from app.services.companion_object_service import CompanionObjectService


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    yield
    get_settings.cache_clear()


def _register_session() -> tuple[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": f"m2_debug_{uuid4().hex[:8]}",
            "password": "safe-password-09",
        },
    )
    assert response.status_code == 200
    body = response.json()
    return body["token"], body["account"]["child_id"]


def _enable_debug(monkeypatch) -> CompanionObjectService:
    monkeypatch.setenv("CHILD_AI_ENVIRONMENT", "dev")
    monkeypatch.setenv("CHILD_AI_ENABLE_DEBUG_TOOLS", "true")
    monkeypatch.setenv("CHILD_AI_DEBUG_TOOLS_TOKEN", "test-debug-token")
    get_settings.cache_clear()
    service = CompanionObjectService(
        repository=InMemoryCompanionObjectRepository(),
    )
    monkeypatch.setattr(debug_api, "companion_object_service", service)
    return service


def _debug_headers(token: str, debug_token: str = "test-debug-token") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Child-AI-Debug-Token": debug_token,
    }


def test_debug_house_object_api_is_disabled_by_default(monkeypatch) -> None:
    token, _ = _register_session()
    monkeypatch.delenv("CHILD_AI_ENABLE_DEBUG_TOOLS", raising=False)
    monkeypatch.delenv("CHILD_AI_DEBUG_TOOLS_TOKEN", raising=False)
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/debug/house-object/create",
        json={
            "visual_kind": "star",
            "state": "co_create",
            "light_location": "窗边",
        },
        headers=_debug_headers(token),
    )

    assert response.status_code == 404


def test_debug_house_object_api_is_unavailable_in_prod(monkeypatch) -> None:
    token, _ = _register_session()
    monkeypatch.setenv("CHILD_AI_ENVIRONMENT", "prod")
    monkeypatch.setenv("CHILD_AI_ENABLE_DEBUG_TOOLS", "true")
    monkeypatch.setenv("CHILD_AI_DEBUG_TOOLS_TOKEN", "test-debug-token")
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/debug/house-object/create",
        json={
            "visual_kind": "star",
            "state": "co_create",
            "light_location": "窗边",
        },
        headers=_debug_headers(token),
    )

    assert response.status_code == 404


def test_debug_house_object_api_requires_matching_token(monkeypatch) -> None:
    token, _ = _register_session()
    _enable_debug(monkeypatch)

    response = client.post(
        "/api/v1/debug/house-object/create",
        json={
            "visual_kind": "star",
            "state": "co_create",
            "light_location": "窗边",
        },
        headers=_debug_headers(token, debug_token="wrong-token"),
    )

    assert response.status_code == 403


def test_debug_create_maps_all_visual_kinds(monkeypatch) -> None:
    token, child_id = _register_session()
    service = _enable_debug(monkeypatch)

    for visual_kind in [
        "star",
        "cloud",
        "paper_boat",
        "tiny_door",
        "dino_shadow",
        "block_light",
    ]:
        response = client.post(
            "/api/v1/debug/house-object/create",
            json={
                "visual_kind": visual_kind,
                "state": "co_create",
                "light_location": "窗边",
            },
            headers=_debug_headers(token),
        )

        assert response.status_code == 200
        companion = response.json()["companion_object"]
        assert companion["visual_kind"] == visual_kind
        assert companion["state"] == "active"
        assert companion["action"] == "co_create"
        active = service.get_active_by_child(child_id)
        assert active is not None
        assert active.child_id == child_id
        assert active.visual_kind == visual_kind


def test_debug_create_supports_seed_and_recall_ui_states(monkeypatch) -> None:
    token, _ = _register_session()
    _enable_debug(monkeypatch)

    seed_response = client.post(
        "/api/v1/debug/house-object/create",
        json={
            "visual_kind": "star",
            "state": "seed",
            "light_location": "窗边",
        },
        headers=_debug_headers(token),
    )
    recall_response = client.post(
        "/api/v1/debug/house-object/create",
        json={
            "visual_kind": "star",
            "state": "recall",
            "light_location": "窗边",
        },
        headers=_debug_headers(token),
    )

    assert seed_response.status_code == 200
    assert seed_response.json()["companion_object"]["state"] == "seed"
    assert seed_response.json()["companion_object"]["action"] == "name_seed"
    assert recall_response.status_code == 200
    assert recall_response.json()["companion_object"]["state"] == "active"
    assert recall_response.json()["companion_object"]["action"] == "recall"


def test_debug_create_rejects_none_state_for_persistence(monkeypatch) -> None:
    token, _ = _register_session()
    _enable_debug(monkeypatch)

    response = client.post(
        "/api/v1/debug/house-object/create",
        json={
            "visual_kind": "star",
            "state": "none",
            "light_location": "窗边",
        },
        headers=_debug_headers(token),
    )

    assert response.status_code == 422


def test_debug_reset_retires_only_current_child(monkeypatch) -> None:
    token_a, child_a = _register_session()
    token_b, child_b = _register_session()
    service = _enable_debug(monkeypatch)

    for token in (token_a, token_b):
        response = client.post(
            "/api/v1/debug/house-object/create",
            json={
                "visual_kind": "star",
                "state": "co_create",
                "light_location": "窗边",
            },
            headers=_debug_headers(token),
        )
        assert response.status_code == 200

    reset_response = client.post(
        "/api/v1/debug/house-object/reset",
        headers=_debug_headers(token_b),
    )

    assert reset_response.status_code == 200
    assert reset_response.json()["retired_count"] == 1
    assert service.get_active_by_child(child_b) is None
    assert service.get_active_by_child(child_a) is not None
