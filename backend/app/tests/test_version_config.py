from pathlib import Path

from app.core.version import load_app_version_config


def test_load_app_version_config_reads_properties(tmp_path: Path) -> None:
    version_file = tmp_path / "app_version.properties"
    version_file.write_text(
        "\n".join(
            [
                "versionCode=9",
                "versionName=1.2.3",
                "updateTitle=发现新版本 v1.2.3",
                "updateContent=第一项\\n第二项",
                "forceUpdate=true",
                "apkFilename=child-ai-test.apk",
            ]
        ),
        encoding="utf-8",
    )

    config = load_app_version_config(version_file)

    assert config.version_code == 9
    assert config.version_name == "1.2.3"
    assert config.update_title == "发现新版本 v1.2.3"
    assert config.update_content == "第一项\n第二项"
    assert config.force_update is True
    assert config.apk_filename == "child-ai-test.apk"


def test_load_app_version_config_uses_safe_defaults_for_missing_file(tmp_path: Path) -> None:
    config = load_app_version_config(tmp_path / "missing.properties")

    assert config.version_code == 2
    assert config.version_name == "0.2.0"
    assert config.apk_filename == "child-ai-companion.apk"
