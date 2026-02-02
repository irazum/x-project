"""AWS Lambda function for image processing on S3 events.

This Lambda function is triggered when an image is uploaded to S3.
It processes the image (resizing, creating thumbnails) and stores the result.

Deploy this function with appropriate IAM permissions for S3 access.
"""

import io
import json
import urllib.parse

import boto3
from PIL import Image

# Configuration
LOGO_MAX_WIDTH = 800
LOGO_MAX_HEIGHT = 800
THUMBNAIL_SIZE = 200

s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Lambda handler for S3 image processing events.

    Args:
        event: S3 event containing bucket and key information
        context: Lambda context

    Returns:
        Response with processing status
    """
    print(f"Received event: {json.dumps(event)}")

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # Skip if not in upload directory or already processed
        if not key.startswith("uploads/logos/") or "_processed" in key:
            print(f"Skipping {key}")
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
    Process an uploaded image - resize and create thumbnail.

    Args:
        bucket: S3 bucket name
        key: S3 object key
    """
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

    # Generate output keys
    base_key = key.rsplit(".", 1)[0]
    main_key = f"{base_key}_processed.jpg"
    thumb_key = f"{base_key}_thumb.jpg"

    # Upload processed images
    upload_image(bucket, main_key, main_image, quality=85)
    upload_image(bucket, thumb_key, thumbnail, quality=80)

    # Optionally delete original
    # s3_client.delete_object(Bucket=bucket, Key=key)


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
