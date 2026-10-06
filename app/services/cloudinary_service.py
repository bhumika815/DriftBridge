import cloudinary
import cloudinary.uploader

from flask import current_app


def configure_cloudinary():
    """Configure Cloudinary using the application's environment settings."""

    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_chat_image(file):
    """
    Upload a chat image to Cloudinary.

    The image is stored inside the DriftBridge chat_images folder.

    Returns:
        str: Secure Cloudinary URL of the uploaded image.
    """

    configure_cloudinary()

    result = cloudinary.uploader.upload(
        file,
        folder="driftbridge/chat_images",
        resource_type="image",
    )

    return result["secure_url"]