import datetime
import io
import uuid
import os

from dotenv import load_dotenv
load_dotenv('backend/.env')

from PIL.Image import Image as Imagetype
from google.cloud import storage
from google.oauth2 import service_account
from loguru import logger  # Added for logging

from src.utils.constants import (
    BUCKET_NAME,
    STAGING_API,
    CDN_API,
    GCP_CREDENTIALS,
)


CONTENT_TYPE = {
    "webp": "image/webp",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "pdf": "application/pdf",
}


def upload_to_gcp(data: Imagetype | bytes | str, extension: str) -> str:
    """
    Upload data to Google Cloud Storage bucket and return the public URL

    Args:
        data: Image object, bytes, or string data to upload
        extension: File extension (determines content type)

    Returns:
        Public URL of the uploaded file

    Raises:
        Exception: If upload fails
    """
    logger.debug(
        f"Starting GCP upload for extension: {extension}, data type: {type(data)}"
    )
    try:
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        random_string = str(uuid.uuid4())

        destination_blob_name = f"{current_time}_{random_string}.{extension}"
        logger.trace(f"Destination blob name: {destination_blob_name}")

        # Determine content type early
        content_type = CONTENT_TYPE.get(extension.lower(), "application/octet-stream")
        logger.trace(f"Determined content type: {content_type}")

        # Handle PIL Image objects specifically
        if isinstance(data, Imagetype):
            logger.trace("Data is PIL Image, converting to bytes...")
            buffer = io.BytesIO()
            # Save based on mode, assume PNG for RGBA, else JPEG
            save_format = "PNG" if data.mode == "RGBA" else "JPEG"
            # Override format if extension dictates (e.g., saving as webp)
            if extension.lower() in ["webp"]:
                save_format = "WEBP"
            elif extension.lower() in ["png"]:
                save_format = "PNG"
            elif extension.lower() in ["jpeg", "jpg"]:
                save_format = "JPEG"

            logger.trace(f"Saving PIL image with format: {save_format}")
            data.save(buffer, format=save_format)
            buffer.seek(0)
            data_bytes = buffer.getvalue()  # Get bytes from PIL Image
            logger.trace(f"PIL Image converted to {len(data_bytes)} bytes.")
        elif isinstance(data, bytes):
            logger.trace("Data is already bytes.")
            data_bytes = data  # If it's already bytes, use it directly
        elif isinstance(data, str):
            # Assuming string data needs to be encoded, e.g., text files
            # This might need adjustment based on expected string input types
            logger.trace("Data is string, encoding to utf-8 bytes...")
            data_bytes = data.encode("utf-8")
        else:
            logger.error(f"Unsupported data type for upload: {type(data)}")
            raise TypeError(f"Unsupported data type for upload: {type(data)}")

        if not data_bytes:
            logger.warning("Data to upload is empty. Skipping upload.")
            # Decide how to handle empty data - raise error or return specific value?
            raise ValueError("Cannot upload empty data to GCP.")

        # Create credentials and client
        logger.trace("Creating GCP service account credentials...")
        if not GCP_CREDENTIALS:
            logger.error("GCP_CREDENTIALS not loaded or is None.")
            raise ValueError("GCP Credentials are not configured.")
        credentials = service_account.Credentials.from_service_account_info(
            GCP_CREDENTIALS
        )
        storage_client = storage.Client(
            credentials=credentials, project=GCP_CREDENTIALS["project_id"]
        )
        logger.trace("GCP Storage client created.")

        # Get bucket and blob
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        logger.trace(f"Obtained blob object: {blob.name} in bucket {BUCKET_NAME}")

        # Set content type metadata (redundant given explicit setting below, but good practice)
        blob.content_type = content_type
        logger.trace(f"Set blob metadata content_type to: {blob.content_type}")

        # Set content disposition
        blob.content_disposition = "inline"  # Or 'attachment' if download is preferred
        logger.trace(
            f"Set blob metadata content_disposition to: {blob.content_disposition}"
        )

        # Upload the data bytes, explicitly providing the content_type
        logger.trace(
            f"Uploading {len(data_bytes)} bytes with explicit content_type: {content_type}..."
        )
        blob.upload_from_string(data_bytes, content_type=content_type)
        logger.info(f"Successfully uploaded {blob.name} to GCP.")

        # Construct and modify the public URL
        url = blob.public_url
        logger.trace(f"Original public URL: {url}")
        if CDN_API != STAGING_API:  # Only replace if CDN_API is different
            url = url.replace(STAGING_API, CDN_API)
            logger.trace(f"Modified URL for CDN: {url}")
        return url

    except Exception as e:
        # Log the error before re-raising
        logger.error(
            f"Error during GCP upload process: {e}", exc_info=True
        )  # Add exc_info for traceback
        # Re-raise with a more informative message, including the original error
        raise Exception(f"Error uploading to GCP: {e}") from e

if __name__=='__main__':
    # --- Test Case 1: Uploading an MP3 audio file ---
    # print("--- Running Test: Upload MP3 Audio ---")
    # try:
    #     with open('audio_generations/97a11425-4029-4320-9737-fd39a0a9f983.mp3', 'rb') as file:
    #         audio_bytes=file.read()
    #     audio_url = upload_to_gcp(data=audio_bytes, extension='mp3')
    #     if audio_url:
    #         print('Successfully Uploaded audio:', audio_url)
    # except FileNotFoundError:
    #     print("SKIPPING: Test audio file not found.")
    # except Exception as e:
    #     print(f"ERROR during audio upload: {e}")

    print("\n" + "="*40 + "\n")

    # --- Test Case 2: Uploading a PDF document ---
    # NOTE: To run this test, create or place a PDF file named 'test_document.pdf'
    # in the same directory as this script.
    print("--- Running Test: Upload PDF Document ---")
    try:
        with open('test_document.pdf', 'rb') as file:
            pdf_bytes=file.read()
        pdf_url = upload_to_gcp(data=pdf_bytes, extension='pdf')
        if pdf_url:
            print('Successfully Uploaded PDF:', pdf_url)
    except FileNotFoundError:
        print("SKIPPING: Test file 'test_document.pdf' not found.")
    except Exception as e:
        print(f"ERROR during PDF upload: {e}")