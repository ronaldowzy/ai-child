from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_download_page_contains_apk_download_and_wechat_hint() -> None:
    response = client.get(
        "/download",
        headers={"user-agent": "MicroMessenger"},
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "小白狐 App 下载" in response.text
    assert "/api/v1/version/download" in response.text
    assert "在浏览器打开" in response.text
    assert 'class="wechat"' in response.text


def test_download_qr_svg_is_generated() -> None:
    response = client.get("/download/qr.svg")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in response.content
