from __future__ import annotations

from html import escape
from io import BytesIO

import qrcode
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from qrcode.image.svg import SvgPathImage

from app.core.config import get_settings
from app.core.version import (
    APK_FILENAME,
    APP_LATEST_VERSION,
    APP_LATEST_VERSION_CODE,
    APP_UPDATE_CONTENT,
    APP_UPDATE_TITLE,
)

router = APIRouter(tags=["download"])


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_download_page(request: Request) -> HTMLResponse:
    return await download_page(request)


@router.get("/download", response_class=HTMLResponse, include_in_schema=False)
async def download_page(request: Request) -> HTMLResponse:
    settings = get_settings()
    apk_path = settings.resolve_repo_path("storage") / "apk" / APK_FILENAME
    apk_exists = apk_path.is_file()
    apk_size_text = _format_file_size(apk_path.stat().st_size) if apk_exists else "暂未生成"
    download_url = str(request.url_for("download_apk"))
    page_url = str(request.url_for("download_page"))
    qr_url = str(request.url_for("download_page_qr"))
    user_agent = request.headers.get("user-agent", "").lower()
    html_class = "wechat" if "micromessenger" in user_agent else ""

    html = f"""<!doctype html>
<html lang="zh-CN" class="{html_class}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>小白狐 App 下载</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #23313f;
      --muted: #637082;
      --line: #d8e1ea;
      --primary: #2977c9;
      --primary-pressed: #1f5f9f;
      --warm: #fff7e8;
      --paper: #f7fbff;
      --card: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: linear-gradient(180deg, #eef7ff 0%, #ffffff 58%, #fffaf0 100%);
      min-height: 100vh;
    }}
    .page {{
      width: min(760px, 100%);
      margin: 0 auto;
      padding: 28px 18px 44px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 22px;
    }}
    .mark {{
      width: 46px;
      height: 46px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      background: #ffffff;
      border: 1px solid var(--line);
      font-size: 25px;
    }}
    h1 {{
      font-size: 28px;
      line-height: 1.2;
      margin: 0 0 4px;
      letter-spacing: 0;
    }}
    .subtitle {{
      color: var(--muted);
      font-size: 15px;
      margin: 0;
    }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 8px 30px rgba(41, 119, 201, 0.08);
    }}
    .version {{
      display: grid;
      gap: 8px;
      margin-bottom: 18px;
    }}
    .version strong {{
      font-size: 20px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 14px;
    }}
    .content {{
      white-space: pre-line;
      line-height: 1.65;
      padding: 14px;
      border: 1px solid #eadcc2;
      background: var(--warm);
      border-radius: 8px;
      margin: 14px 0 18px;
    }}
    .actions {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
      margin: 18px 0;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 12px 18px;
      border-radius: 8px;
      border: 1px solid var(--primary);
      background: var(--primary);
      color: #ffffff;
      text-decoration: none;
      font-weight: 700;
      font-size: 16px;
    }}
    .button:active {{ background: var(--primary-pressed); }}
    .button.disabled {{
      pointer-events: none;
      opacity: 0.55;
      border-color: #9fb1c3;
      background: #9fb1c3;
    }}
    .qr-wrap {{
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 18px;
      align-items: center;
      margin-top: 20px;
      padding: 16px;
      border-radius: 8px;
      background: var(--paper);
      border: 1px solid var(--line);
    }}
    .qr-wrap img {{
      width: 180px;
      height: 180px;
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
    }}
    .hint {{
      color: var(--muted);
      line-height: 1.6;
      font-size: 14px;
    }}
    .wechat-mask {{
      display: none;
      position: fixed;
      inset: 0;
      z-index: 20;
      background: rgba(21, 30, 40, 0.88);
      color: #ffffff;
      padding: 24px;
    }}
    .wechat .wechat-mask {{ display: block; }}
    .arrow {{
      position: absolute;
      right: 22px;
      top: 12px;
      font-size: 42px;
      line-height: 1;
    }}
    .wechat-box {{
      margin-top: 70px;
      border: 1px solid rgba(255,255,255,0.4);
      border-radius: 8px;
      padding: 18px;
      background: rgba(255,255,255,0.08);
      line-height: 1.7;
    }}
    @media (max-width: 620px) {{
      h1 {{ font-size: 24px; }}
      .qr-wrap {{
        grid-template-columns: 1fr;
        justify-items: center;
        text-align: center;
      }}
      .panel {{ padding: 16px; }}
    }}
  </style>
  <script>
    (function () {{
      var ua = navigator.userAgent || "";
      if (/MicroMessenger/i.test(ua)) {{
        document.documentElement.classList.add("wechat");
      }}
    }})();
  </script>
</head>
<body>
  <div class="wechat-mask" role="dialog" aria-label="微信打开提示">
    <div class="arrow">↗</div>
    <div class="wechat-box">
      <strong>请用手机自带浏览器打开</strong><br />
      在微信里请点右上角 “...” ，选择“在浏览器打开”，再点击下载 APK。
    </div>
  </div>
  <main class="page">
    <section class="brand">
      <div class="mark" aria-hidden="true">狐</div>
      <div>
        <h1>小白狐 App 下载</h1>
        <p class="subtitle">Android 家庭内测安装包</p>
      </div>
    </section>
    <section class="panel">
      <div class="version">
        <strong>{escape(APP_UPDATE_TITLE)}</strong>
        <span class="meta">版本 {escape(APP_LATEST_VERSION)} / versionCode {APP_LATEST_VERSION_CODE} / APK {escape(apk_size_text)}</span>
      </div>
      <div class="content">{escape(APP_UPDATE_CONTENT)}</div>
      <div class="actions">
        <a class="button{' disabled' if not apk_exists else ''}" href="{escape(download_url)}">
          {'APK 暂未准备好' if not apk_exists else '下载 Android APK'}
        </a>
      </div>
      <div class="qr-wrap">
        <img src="{escape(qr_url)}" alt="下载页二维码" />
        <p class="hint">
          用手机自带浏览器扫码打开下载页。<br />
          如果在微信里打开，请点右上角 “...” ，选择“在浏览器打开”。<br />
          下载页地址：{escape(page_url)}
        </p>
      </div>
    </section>
  </main>
</body>
</html>
"""
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/download/qr.svg", include_in_schema=False, name="download_page_qr")
async def download_page_qr(request: Request) -> Response:
    page_url = str(request.url_for("download_page"))
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(page_url)
    qr.make(fit=True)
    image = qr.make_image(image_factory=SvgPathImage)
    output = BytesIO()
    image.save(output)
    return Response(
        content=output.getvalue(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-store"},
    )


def _format_file_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"
