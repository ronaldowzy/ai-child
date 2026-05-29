#!/usr/bin/env python3
"""Convert states-v2 PNG frames to 512px WebP frame sequences for Android assets.

Usage:
    python3 scripts/convert_states_v2.py [--states idle listening speaking] [--quality 75] [--size 512]
"""
import argparse
import json
import os
import shutil
from pathlib import Path
from PIL import Image

STATES_V2_DIR = Path("/Users/wzy/Downloads/states-v2")
OUTPUT_BASE = Path("android/app/src/main/assets/mascot/xiaobaohu/v2")

DEFAULT_STATES = ["idle", "listening", "speaking"]
TARGET_SIZE = 512
WEBP_QUALITY = 75


def convert_state(state: str, quality: int, size: int) -> dict:
    src_dir = STATES_V2_DIR / state / "v0.1.0" / "frames"
    if not src_dir.exists():
        raise FileNotFoundError(f"Source frames not found: {src_dir}")

    src_manifest_path = STATES_V2_DIR / state / "v0.1.0" / "manifest.json"
    with open(src_manifest_path) as f:
        src_manifest = json.load(f)

    dst_dir = OUTPUT_BASE / state / "v2.0.0" / "frames_webp"
    dst_dir.mkdir(parents=True, exist_ok=True)

    frame_files = sorted(src_dir.glob("*.png"))
    if not frame_files:
        raise FileNotFoundError(f"No PNG frames in {src_dir}")

    converted = 0
    total_bytes = 0
    for i, frame_path in enumerate(frame_files, 1):
        img = Image.open(frame_path)
        if img.width != size or img.height != size:
            img = img.resize((size, size), Image.LANCZOS)
        out_name = f"fox_{state}_{i:04d}.webp"
        out_path = dst_dir / out_name
        img.save(str(out_path), "WEBP", quality=quality, method=4)
        total_bytes += out_path.stat().st_size
        converted += 1

    return {
        "state": state,
        "frames_converted": converted,
        "total_bytes": total_bytes,
        "avg_frame_bytes": total_bytes // converted if converted else 0,
        "output_dir": str(dst_dir),
    }


def create_state_manifest(state: str, frame_count: int, size: int) -> Path:
    manifest = {
        "state": state,
        "displayName": f"fox_{state}",
        "version": "v2.0.0",
        "type": "frame_sequence",
        "fps": 12,
        "frameCount": frame_count,
        "loop": True,
        "width": size,
        "height": size,
        "path": f"{state}/v2.0.0/",
        "manifest": f"{state}/v2.0.0/manifest.json",
        "framePattern": f"frames_webp/fox_{state}_%04d.webp",
        "format": "webp",
        "runtimeOnly": True,
    }
    out_path = OUTPUT_BASE / state / "v2.0.0" / "manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return out_path


def create_mascot_manifest(states: list[str], frame_count: int, size: int) -> Path:
    states_dict = {}
    for state in states:
        states_dict[state] = {
            "version": "v2.0.0",
            "type": "loop",
            "fps": 12,
            "frameCount": frame_count,
            "width": size,
            "height": size,
            "path": f"{state}/v2.0.0/",
            "manifest": f"{state}/v2.0.0/manifest.json",
            "framePattern": f"frames_webp/fox_{state}_%04d.webp",
        }

    manifest = {
        "mascot": "Little White Fox",
        "assetPackageVersion": "0.2.0-v2-states",
        "format": "webp_frame_sequence_runtime",
        "defaultFps": 12,
        "defaultState": "idle",
        "dimensions": [{"width": size, "height": size}],
        "states": states_dict,
        "statePriority": [
            "safety_concern", "privacy_boundary", "network_error",
            "speaking", "thinking", "listening", "homework_focus",
            "calm", "sleepy", "jumping_happy", "idle",
        ],
        "notes": "v2 mascot package: 512px WebP frame sequences from states-v2 assets.",
    }
    out_path = OUTPUT_BASE / "mascot_manifest.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Convert states-v2 to Android WebP frames")
    parser.add_argument("--states", nargs="+", default=DEFAULT_STATES)
    parser.add_argument("--quality", type=int, default=WEBP_QUALITY)
    parser.add_argument("--size", type=int, default=TARGET_SIZE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"States: {args.states}")
    print(f"Target: {args.size}x{args.size}, WebP quality={args.quality}")
    print(f"Source: {STATES_V2_DIR}")
    print(f"Output: {OUTPUT_BASE}")
    print()

    if args.dry_run:
        for state in args.states:
            src_dir = STATES_V2_DIR / state / "v0.1.0" / "frames"
            count = len(list(src_dir.glob("*.png"))) if src_dir.exists() else 0
            print(f"  {state}: {count} PNG frames would be converted")
        return

    results = []
    for state in args.states:
        print(f"Converting {state}...")
        result = convert_state(state, args.quality, args.size)
        results.append(result)
        print(f"  {result['frames_converted']} frames, "
              f"{result['total_bytes'] / 1024:.0f} KB total, "
              f"~{result['avg_frame_bytes'] / 1024:.1f} KB/frame")

        create_state_manifest(state, result["frames_converted"], args.size)

    create_mascot_manifest(args.states, 48, args.size)

    total = sum(r["total_bytes"] for r in results)
    print(f"\nTotal: {total / 1024 / 1024:.2f} MB for {len(args.states)} states")
    print(f"Full 10-state estimate: {total / len(args.states) * 10 / 1024 / 1024:.2f} MB")
    print(f"\nOutput written to: {OUTPUT_BASE}")


if __name__ == "__main__":
    main()
