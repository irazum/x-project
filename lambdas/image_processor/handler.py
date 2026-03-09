"""AWS Lambda function for image processing on S3 events.

This Lambda function is triggered when an image is uploaded to the
`uploads/logos/` prefix in S3. It processes the image (resize + thumbnail)
and writes results to the `logos/` prefix — which does NOT trigger this
Lambda again, avoiding infinite loops.

Convention-based paths:
  API uploads to:  uploads/logos/{project_id}/original.jpg  → triggers Lambda
  Lambda writes:   logos/{project_id}/logo.jpg               (no trigger)
                   logos/{project_id}/thumb.jpg               (no trigger)

The S3 event notification must be configured with prefix filter: uploads/logos/
"""

import io
import json
import os
import re
import urllib.parse
from typing import Any

import boto3
from PIL import Image

# Configuration — should match app/core/config.py defaults
LOGO_MAX_WIDTH = int(os.environ.get("LOGO_MAX_WIDTH", "800"))
LOGO_MAX_HEIGHT = int(os.environ.get("LOGO_MAX_HEIGHT", "800"))
THUMBNAIL_SIZE = int(os.environ.get("LOGO_THUMBNAIL_SIZE", "200"))
UPLOAD_PREFIX = os.environ.get("LOGO_UPLOAD_PREFIX", "uploads/logos")
PROCESSED_PREFIX = os.environ.get("LOGO_PROCESSED_PREFIX", "logos")

s3_client = boto3.client("s3")


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """
    Lambda handler for S3 image processing events.

    Args:
        event: S3 event containing bucket and key information
        _context: Lambda context (unused)

    Returns:
        Response with processing status
    """
    print(f"Received event: {json.dumps(event)}")

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # Only process files in uploads/logos/ prefix
        if not key.startswith(f"{UPLOAD_PREFIX}/"):
            print(f"Skipping {key} — not in {UPLOAD_PREFIX}/")
            continue

        try:
            process_image(bucket, key)
            print(f"Successfully processed {key}")
        except Exception as e:
            print(f"Error processing {key}: {e}")
            raise

    return {
        "statusCode": 200,
        "body": json.dumps("Processing complete"),
    }


def process_image(bucket: str, key: str) -> None:
    """
    Process an uploaded image — resize and create thumbnail.

    Input key:   uploads/logos/{project_id}/original.jpg
    Output keys: logos/{project_id}/logo.jpg
                 logos/{project_id}/thumb.jpg

    Args:
        bucket: S3 bucket name
        key: S3 object key (under uploads/logos/)
    """
    # Extract project_id from key
    match = re.match(rf"{re.escape(UPLOAD_PREFIX)}/(\d+)/", key)
    if not match:
        print(f"Could not extract project_id from key: {key}")
        return

    project_id = match.group(1)

    # Download the image
    response = s3_client.get_object(Bucket=bucket, Key=key)
    image_content = response["Body"].read()

    # Open with PIL
    image = Image.open(io.BytesIO(image_content))

    # Convert RGBA/P to RGB
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Resize main image
    main_image = resize_image(image, LOGO_MAX_WIDTH, LOGO_MAX_HEIGHT)

    # Create thumbnail
    thumbnail = create_thumbnail(image, THUMBNAIL_SIZE)

    # Convention-based output paths
    logo_key = f"{PROCESSED_PREFIX}/{project_id}/logo.jpg"
    thumb_key = f"{PROCESSED_PREFIX}/{project_id}/thumb.jpg"

    # Upload processed images
    upload_image(bucket, logo_key, main_image, quality=85)
    upload_image(bucket, thumb_key, thumbnail, quality=80)


def resize_image(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """Resize image to fit within max dimensions."""
    if image.width <= max_width and image.height <= max_height:
        return image.copy()

    ratio = min(max_width / image.width, max_height / image.height)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def create_thumbnail(image: Image.Image, size: int) -> Image.Image:
    """Create a square center-cropped thumbnail."""
    width, height = image.size
    min_dim = min(width, height)

    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim

    cropped = image.crop((left, top, right, bottom))
    return cropped.resize((size, size), Image.Resampling.LANCZOS)


def upload_image(bucket: str, key: str, image: Image.Image, quality: int = 85) -> None:
    """Upload PIL image to S3."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer,
        ContentType="image/jpeg",
    )
