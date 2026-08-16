import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


# Directory where processed profile pictures will be stored
PROFILE_PICS_DIR = Path("media/profile_pics")


# Image processing with Pillow is CPU-bound work,
# so this function should be executed in a thread pool
# when called from an async FastAPI endpoint.
def process_profile_image(content: bytes) -> str:
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

        # Build the complete path where the image will be saved
        filepath = PROFILE_PICS_DIR / filename

        # Create the profile pictures directory if it does not already exist
        PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)

        # Save the processed image as an optimized JPEG
        img.save(
            filepath,
            "JPEG",
            quality=85,
            optimize=True,
        )

    # Store this filename in the user's database record
    return filename


def delete_profile_image(filename: str | None) -> None:
    """Delete an existing profile image from storage."""

    # Nothing to delete if the user does not have a profile image
    if filename is None:
        return

    # Build the complete path of the existing profile image
    filepath = PROFILE_PICS_DIR / filename

    # Delete the file only if it exists
    if filepath.exists():
        filepath.unlink()