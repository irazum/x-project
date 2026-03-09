#!/usr/bin/env bash
# Build the Pillow Lambda layer zip for Python 3.14.
# Requires Docker to produce a linux/x86_64-compatible wheel.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAYER_DIR="$SCRIPT_DIR/layers"
OUTPUT="$LAYER_DIR/pillow.zip"

mkdir -p "$LAYER_DIR"
rm -f "$OUTPUT"

echo "Building Pillow layer..."

# Use the official Lambda Python 3.14 image to install Pillow
docker run --rm \
  --platform linux/amd64 \
  --entrypoint bash \
  -v "$LAYER_DIR:/out" \
  public.ecr.aws/lambda/python:3.14 \
  -c "
    pip install 'pillow>=10.2.0' -t /tmp/python && \
    cd /tmp && \
    python -c \"
import zipfile, os
with zipfile.ZipFile('/out/pillow.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('python'):
        for f in files:
            fpath = os.path.join(root, f)
            zf.write(fpath)
\"
  "

echo "Layer built: $OUTPUT ($(du -h "$OUTPUT" | cut -f1))"
