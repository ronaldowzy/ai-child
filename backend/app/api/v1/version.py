"""版本检查与 APK 下载 API"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.version import (
    APK_FILENAME,
    APP_FORCE_UPDATE,
    APP_LATEST_VERSION,
    APP_LATEST_VERSION_CODE,
    APP_UPDATE_CONTENT,
    APP_UPDATE_TITLE,
)

router = APIRouter(prefix="/version", tags=["version"])


class VersionCheckResponse(BaseModel):
    """版本检查响应"""

    versionName: str
    versionCode: int
    title: str
    content: str
    forceUpdate: bool
    downloadUrl: str


@router.get("/check", response_model=VersionCheckResponse)
async def check_version() -> VersionCheckResponse:
    """检查最新版本信息"""
    return VersionCheckResponse(
        versionName=APP_LATEST_VERSION,
        versionCode=APP_LATEST_VERSION_CODE,
        title=APP_UPDATE_TITLE,
        content=APP_UPDATE_CONTENT,
        forceUpdate=APP_FORCE_UPDATE,
        downloadUrl="/api/v1/version/download",
    )


@router.get("/download")
async def download_apk() -> FileResponse:
    """下载最新 APK 文件"""
    settings = get_settings()
    apk_path = settings.resolve_repo_path("storage") / "apk" / APK_FILENAME

    if not apk_path.is_file():
        raise HTTPException(status_code=404, detail="APK 文件不存在")

    return FileResponse(
        path=apk_path,
        filename=APK_FILENAME,
        media_type="application/vnd.android.package-archive",
    )
