import uuid
from io import BytesIO

import boto3
from starlette.concurrency import run_in_threadpool
from .config import settings

from PIL import Image, ImageOps


# # Directory where processed profile pictures will be stored
# PROFILE_PICS_DIR = Path("media/profile_pics")

def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=(
            settings.s3_access_key_id.get_secret_value()
            if settings.s3_access_key_id
            else None
        ),
        aws_secret_access_key=(
            settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key
            else None
        ),
        endpoint_url=settings.s3_endpoint_url,
    )


# Image processing with Pillow is CPU-bound work,
# so this function should be executed in a thread pool
# when called from an async FastAPI endpoint.
def process_profile_image(content: bytes) -> tuple[bytes, str]:
    """Process and save a profile image, returning the generated filename."""

    # Open the image directly from the uploaded byte content
    with Image.open(BytesIO(content)) as original:

        # Correct image orientation using EXIF metadata
        img = ImageOps.exif_transpose(original)

        # Resize and crop the image to a fixed 300x300 square
        # LANCZOS provides high-quality image resizing
        img = ImageOps.fit(
            img,
            (300, 300),
            method=Image.Resampling.LANCZOS,
        )

        # Convert images with transparency or palette mode to RGB
        # because JPEG does not support transparency
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        # Generate a unique filename to prevent filename collisions
        filename = f"{uuid.uuid4().hex}.jpg"

        output=BytesIO()

        # Save the processed image as an optimized JPEG
        img.save(output, "JPEG", quality=85, optimize=True)
        output.seek(0)

    return output.read(), filename

def _upload_to_s3(file_bytes: bytes, key: str) -> None:
    s3 = _get_s3_client()
    s3.upload_fileobj(
        BytesIO(file_bytes),
        settings.s3_bucket_name,
        key,
        ExtraArgs={"ContentType": "image/jpeg"},
    )
def _delete_from_s3(key: str) -> None:
    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.s3_bucket_name, Key=key)

async def upload_profile_image(file_bytes: bytes, filename: str) -> None:
    key = f"profile_pics/{filename}"
    await run_in_threadpool(_upload_to_s3, file_bytes, key)
async def delete_profile_image(filename: str | None) -> None:
    if filename is None:
        return
    key = f"profile_pics/{filename}"
    await run_in_threadpool(_delete_from_s3, key)