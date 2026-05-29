from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import repo_root

router = APIRouter(prefix="/assets/fox", tags=["fox-assets"])

VALID_STATES = frozenset({
    "listening",
    "speaking",
    "waiting_soft",
    "thinking",
    "preparing_speech",
    "image_viewing",
    "co_create",
    "paused",
    "retry",
})


def _hd_dir() -> Path:
    return (repo_root() / "storage" / "fox_hd").resolve()


@router.get("/hd/manifest")
def get_hd_manifest() -> JSONResponse:
    """Return available HD packages with sizes and checksums."""
    import hashlib

    hd_dir = _hd_dir()
    packages = {}
    if hd_dir.exists():
        for state in sorted(VALID_STATES):
            zip_path = hd_dir / f"{state}_hd.zip"
            if zip_path.exists():
                sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()
                packages[state] = {
                    "url": f"/api/v1/assets/fox/hd/{state}",
                    "sizeBytes": zip_path.stat().st_size,
                    "checksum": f"sha256:{sha256}",
                }
    return JSONResponse(content={"packages": packages})


@router.get("/hd/{state}")
def download_hd_package(state: str) -> FileResponse:
    """Download HD WebP zip for a specific state."""
    if state not in VALID_STATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown state: {state}",
        )

    hd_dir = _hd_dir()
    zip_path = hd_dir / f"{state}_hd.zip"
    if not zip_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{state}_hd.zip",
    )
