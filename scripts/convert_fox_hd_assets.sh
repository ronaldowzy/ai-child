#!/usr/bin/env bash
# Convert 1024px PNG frames to WebP zip packages for on-demand HD download.
# Input:  /Users/wzy/Downloads/states-v2/{state}/v0.1.0/frames/*.png
# Output: backend/storage/fox_hd/{state}_hd.zip  (contains frames_webp/ + manifest.json)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="/Users/wzy/Downloads/states-v2"
OUTPUT_DIR="$REPO_ROOT/storage/fox_hd"
TMP_DIR="/tmp/fox_hd_convert"
WEBP_QUALITY=80

STATES=(listening speaking waiting_soft thinking preparing_speech image_viewing co_create paused retry)

if ! command -v cwebp &>/dev/null; then
    echo "ERROR: cwebp not found. Install with: brew install webp"
    exit 1
fi

mkdir -p "$OUTPUT_DIR" "$TMP_DIR"

total_original_bytes=0
total_webp_bytes=0

for state in "${STATES[@]}"; do
    src_frames="$SOURCE_DIR/$state/v0.1.0/frames"
    if [[ ! -d "$src_frames" ]]; then
        echo "SKIP $state: source dir not found"
        continue
    fi

    state_tmp="$TMP_DIR/$state"
    frames_out="$state_tmp/frames_webp"
    rm -rf "$state_tmp"
    mkdir -p "$frames_out"

    echo "=== Converting $state ==="

    frame_count=0
    state_original=0
    for png in "$src_frames"/*.png; do
        frame_count=$((frame_count + 1))
        frame_num=$(printf "%04d" "$frame_count")
        original_size=$(stat -f%z "$png" 2>/dev/null || stat -c%s "$png" 2>/dev/null)
        state_original=$((state_original + original_size))

        cwebp -q $WEBP_QUALITY -m 4 "$png" -o "$frames_out/fox_${state}_${frame_num}.webp" 2>/dev/null
    done

    # Get frame pattern from existing manifest or use default
    frame_pattern="frames_webp/fox_${state}_%04d.webp"

    # Write per-state manifest
    cat > "$state_tmp/manifest.json" <<MANIFEST
{
  "state": "$state",
  "displayName": "fox_$state",
  "version": "v2.0.0-hd",
  "type": "frame_sequence",
  "fps": 12,
  "frameCount": $frame_count,
  "loop": true,
  "width": 1024,
  "height": 1024,
  "path": "$state/v2.0.0-hd/",
  "manifest": "$state/v2.0.0-hd/manifest.json",
  "framePattern": "$frame_pattern",
  "format": "webp",
  "runtimeOnly": true
}
MANIFEST

    # Create zip
    zip_name="${state}_hd.zip"
    (cd "$state_tmp" && zip -r "$OUTPUT_DIR/$zip_name" frames_webp/ manifest.json -q)

    zip_size=$(stat -f%z "$OUTPUT_DIR/$zip_name" 2>/dev/null || stat -c%s "$OUTPUT_DIR/$zip_name" 2>/dev/null)
    total_original_bytes=$((total_original_bytes + state_original))
    total_webp_bytes=$((total_webp_bytes + zip_size))

    # Human readable sizes
    original_hr=$(echo "$state_original" | awk '{ split("B KB MB GB", v); s=1; while($1>=1024 && s<4) {$1/=1024; s++} printf "%.1f%s", $1, v[s] }')
    zip_hr=$(echo "$zip_size" | awk '{ split("B KB MB GB", v); s=1; while($1>=1024 && s<4) {$1/=1024; s++} printf "%.1f%s", $1, v[s] }')
    echo "  $state: $frame_count frames, PNG $original_hr -> WebP zip $zip_hr"
done

echo ""
echo "=== Summary ==="
original_hr=$(echo "$total_original_bytes" | awk '{ split("B KB MB GB", v); s=1; while($1>=1024 && s<4) {$1/=1024; s++} printf "%.1f%s", $1, v[s] }')
zip_hr=$(echo "$total_webp_bytes" | awk '{ split("B KB MB GB", v); s=1; while($1>=1024 && s<4) {$1/=1024; s++} printf "%.1f%s", $1, v[s] }')
echo "Total original PNG: $original_hr"
echo "Total WebP zips:    $zip_hr"
echo "Output: $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR/"*_hd.zip 2>/dev/null || true

# Clean up tmp
rm -rf "$TMP_DIR"
echo "Done."
