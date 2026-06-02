"""
应用版本配置。

Android 和后端版本检查共用 release/app_version.properties。正式发版前
必须递增 versionCode，并把同版本 APK 放到 storage/apk/。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppVersionConfig:
    version_name: str
    version_code: int
    update_title: str
    update_content: str
    force_update: bool
    apk_filename: str


def load_app_version_config(version_file: Path | None = None) -> AppVersionConfig:
    repo_root = Path(__file__).resolve().parents[3]
    path = version_file or repo_root / "release" / "app_version.properties"
    values = _load_properties(path)

    version_name = values.get("versionName", "0.2.0")
    version_code = _parse_int(values.get("versionCode"), default=2)
    return AppVersionConfig(
        version_name=version_name,
        version_code=version_code,
        update_title=values.get("updateTitle", f"发现新版本 v{version_name}"),
        update_content=values.get("updateContent", "修复了一些问题").replace("\\n", "\n"),
        force_update=values.get("forceUpdate", "false").strip().lower() == "true",
        apk_filename=values.get("apkFilename", "child-ai-companion.apk"),
    )


def _load_properties(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return values


def _parse_int(raw_value: str | None, *, default: int) -> int:
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


_APP_VERSION_CONFIG = load_app_version_config()

# 当前最新版本号
APP_LATEST_VERSION = _APP_VERSION_CONFIG.version_name
APP_LATEST_VERSION_CODE = _APP_VERSION_CONFIG.version_code

# 更新提示内容
APP_UPDATE_TITLE = _APP_VERSION_CONFIG.update_title
APP_UPDATE_CONTENT = _APP_VERSION_CONFIG.update_content

# 是否强制更新（true 时用户必须更新才能使用）
APP_FORCE_UPDATE = _APP_VERSION_CONFIG.force_update

# APK 文件名（放在 storage/apk/ 目录下）
APK_FILENAME = _APP_VERSION_CONFIG.apk_filename
