from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import repo_root
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _make_hd_zip(state: str, frame_count: int = 3) -> bytes:
    """Create a minimal valid HD zip for testing."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("frames_webp/", "")
        for i in range(1, frame_count + 1):
            zf.writestr(
                f"frames_webp/fox_{state}_{i:04d}.webp",
                b"RIFF" + b"\x00" * 10,
            )
        zf.writestr(
            "manifest.json",
            f'{{"state":"{state}","frameCount":{frame_count}}}',
        )
    return buf.getvalue()


@pytest.fixture()
def hd_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use a temp dir for HD assets and patch _hd_dir to point there."""
    hd_dir = tmp_path / "storage" / "fox_hd"
    hd_dir.mkdir(parents=True)

    import app.api.fox_assets as fox_module

    monkeypatch.setattr(fox_module, "_hd_dir", lambda: hd_dir)
    return hd_dir


VALID_STATES = [
    "listening",
    "speaking",
    "waiting_soft",
    "thinking",
    "preparing_speech",
    "image_viewing",
    "co_create",
    "paused",
    "retry",
]


class TestFoxHdDownload:
    def test_download_returns_zip_for_valid_state(
        self, client: TestClient, hd_dir: Path
    ) -> None:
        zip_data = _make_hd_zip("listening")
        (hd_dir / "listening_hd.zip").write_bytes(zip_data)

        resp = client.get("/api/v1/assets/fox/hd/listening")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        assert resp.content == zip_data

    def test_download_returns_404_for_unknown_state(
        self, client: TestClient, hd_dir: Path
    ) -> None:
        resp = client.get("/api/v1/assets/fox/hd/unknown_state")
        assert resp.status_code == 404

    def test_download_returns_404_for_idle(
        self, client: TestClient, hd_dir: Path
    ) -> None:
        resp = client.get("/api/v1/assets/fox/hd/idle")
        assert resp.status_code == 404

    def test_download_returns_404_when_zip_missing(
        self, client: TestClient, hd_dir: Path
    ) -> None:
        resp = client.get("/api/v1/assets/fox/hd/listening")
        assert resp.status_code == 404

    @pytest.mark.parametrize("state", VALID_STATES)
    def test_all_valid_states_accepted(
        self, client: TestClient, hd_dir: Path, state: str
    ) -> None:
        zip_data = _make_hd_zip(state)
        (hd_dir / f"{state}_hd.zip").write_bytes(zip_data)

        resp = client.get(f"/api/v1/assets/fox/hd/{state}")
        assert resp.status_code == 200


class TestFoxHdManifest:
    def test_manifest_lists_available_packages(
        self, client: TestClient, hd_dir: Path
    ) -> None:
        for state in ["listening", "speaking"]:
            (hd_dir / f"{state}_hd.zip").write_bytes(_make_hd_zip(state))

        resp = client.get("/api/v1/assets/fox/hd/manifest")
        assert resp.status_code == 200
        body = resp.json()
        assert "packages" in body
        assert "listening" in body["packages"]
        assert "speaking" in body["packages"]
        assert "thinking" not in body["packages"]

    def test_manifest_includes_size_and_checksum(
        self, client: TestClient, hd_dir: Path
    ) -> None:
        zip_data = _make_hd_zip("listening")
        (hd_dir / "listening_hd.zip").write_bytes(zip_data)

        resp = client.get("/api/v1/assets/fox/hd/manifest")
        pkg = resp.json()["packages"]["listening"]
        assert pkg["sizeBytes"] == len(zip_data)
        assert pkg["checksum"].startswith("sha256:")
        assert len(pkg["checksum"]) == len("sha256:") + 64

    def test_manifest_empty_when_no_packages(
        self, client: TestClient, hd_dir: Path
    ) -> None:
        resp = client.get("/api/v1/assets/fox/hd/manifest")
        assert resp.status_code == 200
        assert resp.json()["packages"] == {}
