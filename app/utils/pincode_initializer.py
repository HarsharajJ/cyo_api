import os
import pandas as pd
from sqlalchemy import inspect, select
from app.database import engine, SessionLocal
from app.models.pincode import Pincode
from typing import Optional


def initialize_pincodes():
    """
    Check if 'pincodes' table exists and has data.
    If not, create the table and populate with data from Zipcode.csv
    """
    inspector = inspect(engine)

    table_exists = "pincodes" in inspector.get_table_names()

    # Reflect metadata only if the table exists
    if table_exists:
        print("Pincodes table exists, checking if it's empty...")
        with engine.connect() as conn:
            result = conn.execute(select(Pincode).limit(1)).fetchone()
            if result:
                print("Pincodes table already populated, skipping initialization")
                return
            else:
                print("Pincodes table is empty, proceeding with initialization...")
    else:
        print("Pincodes table not found, creating and initializing...")

    # Get the path to the CSV file
    csv_path = os.path.join(os.path.dirname(__file__), "..", "models", "Zipcode.csv")

    if not os.path.exists(csv_path):
        print(f"⚠️  Warning: Zipcode.csv not found at {csv_path}")
        return

    try:
        # Read CSV file
        df = pd.read_csv(csv_path)

        # Create tables if they don't exist
        from app.database import Base
        Base.metadata.create_all(bind=engine)

        # Insert data in batches
        db = SessionLocal()
        try:
            batch_size = 1000
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]

                pincode_objects = [
                    Pincode(
                        district=row['District'],
                        state_name=row['StateName'],
                        latitude=float(row['Latitude']),
                        longitude=float(row['Longitude']),
                        pincode=str(row['Pincode'])
                    )
                    for _, row in batch.iterrows()
                ]

                db.bulk_save_objects(pincode_objects)
                db.commit()
                print(f"✅ Inserted batch {i // batch_size + 1}/{(len(df) // batch_size) + 1}")

            print(f"🎉 Successfully inserted {len(df)} pincodes into database")

        except Exception as e:
            db.rollback()
            print(f"❌ Error inserting pincodes: {e}")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error reading CSV or initializing pincodes: {e}")


# --- Storage helpers and shared save_image ---
try:
    from google.cloud import storage  # type: ignore
except Exception:
    storage = None

from app.config import settings


def check_storage_connection_and_ensure_bucket(bucket_name: Optional[str] = None) -> str:
    """
    Ensure the storage client can connect and the bucket exists (create if missing).

    Reads bucket name from GCP_BUCKET_NAME env var if not supplied.
    Raises RuntimeError on failure. Returns the bucket name on success.
    """
    # Try OS env first, then pydantic settings (which reads .env)
    env_bucket = os.environ.get("GCP_BUCKET_NAME") or settings.gcp_bucket_name
    if bucket_name is None:
        if not env_bucket:
            raise RuntimeError("GCP bucket name not provided. Set GCP_BUCKET_NAME in your .env or settings")
        bucket_name = env_bucket

    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Add it to requirements.txt and install.")

    if not settings.gcp_service_account_file:
        raise RuntimeError("GCP service account file not provided. Set GCP_SERVICE_ACCOUNT_FILE in your .env or settings")

    client = storage.Client.from_service_account_json(settings.gcp_service_account_file)
    bucket = client.bucket(bucket_name)
    try:
        if not bucket.exists():
            bucket.create()
            # Enable Uniform Bucket-Level Access
            bucket.iam_configuration.uniform_bucket_level_access_enabled = True
            bucket.patch()
            # Grant public read access via IAM (works with UBLA)
            policy = bucket.get_iam_policy(requested_policy_version=3)
            # Add public read role only if not already present
            if not any(b for b in policy.bindings if b["role"] == "roles/storage.objectViewer" and "allUsers" in b["members"]):
                policy.bindings.append({
                    "role": "roles/storage.objectViewer",
                    "members": {"allUsers"}
                })
                bucket.set_iam_policy(policy)
    except Exception as e:
        raise RuntimeError(f"Unable to access/create bucket '{bucket_name}': {e}")

    return bucket_name


def get_storage_bucket(bucket_name: Optional[str] = None):
    """Return a google.cloud.storage.Bucket instance for the configured bucket."""
    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Add it to requirements.txt and install.")

    env_bucket = os.environ.get("GCP_BUCKET_NAME") or settings.gcp_bucket_name
    if bucket_name is None:
        if not env_bucket:
            raise RuntimeError("GCP bucket name not provided. Set GCP_BUCKET_NAME in your .env or settings")
        bucket_name = env_bucket

    if not settings.gcp_service_account_file:
        raise RuntimeError("GCP service account file not provided. Set GCP_SERVICE_ACCOUNT_FILE in your .env or settings")

    client = storage.Client.from_service_account_json(settings.gcp_service_account_file)
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        bucket.create()
        # Enable Uniform Bucket-Level Access
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket.patch()
        # Grant public read access via IAM (works with UBLA)
        policy = bucket.get_iam_policy(requested_policy_version=3)
        # Add public read role only if not already present
        if not any(b for b in policy.bindings if b["role"] == "roles/storage.objectViewer" and "allUsers" in b["members"]):
            policy.bindings.append({
                "role": "roles/storage.objectViewer",
                "members": {"allUsers"}
            })
            bucket.set_iam_policy(policy)
    return bucket


def save_image(file, path: str, bucket_name: Optional[str] = None) -> Optional[str]:
    """
    Save an UploadFile to GCP storage after resizing.

    Returns the public URL to store in DB, or None if no file was provided.
    """
    # Handle None or empty string (swagger sends empty string when field is present but empty)
    if not file:
        return None
    if isinstance(file, str):
        if file.strip() == "":
            return None
        return file

    filename = getattr(file, "filename", None)
    if not filename:
        return None

    normalized = path.lstrip("/")

    # GCP upload only.
    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Install it and try again.")

    if not settings.gcp_service_account_file:
        raise RuntimeError("GCP service account file not configured. Set GCP_SERVICE_ACCOUNT_FILE in .env")

    if not (bucket_name or os.environ.get("GCP_BUCKET_NAME") or settings.gcp_bucket_name):
        raise RuntimeError("GCP bucket not configured. Set GCP_BUCKET_NAME in .env or pass bucket_name")

    try:
        bucket = get_storage_bucket(bucket_name)
        blob = bucket.blob(normalized)
        
        # Resize image
        resized_file = resize_image(file.file)
        blob.upload_from_file(resized_file, rewind=True)
        
        # Construct public URL
        public_url = f"https://storage.googleapis.com/{bucket.name}/{blob.name}"
        return public_url
    except Exception as e:
        raise RuntimeError(f"GCP upload failed: {e}")


def save_images(files, base_path: str, bucket_name: Optional[str] = None) -> list[str]:
    """
    Save multiple UploadFiles to GCP storage efficiently.

    Args:
        files: List of UploadFile objects or single UploadFile
        base_path: Base path template (should include placeholders for indexing)
        bucket_name: Optional bucket name override

    Returns:
        List of public URLs for the uploaded files
    """
    # Handle single file case
    if not isinstance(files, list):
        files = [files]

    # Filter out None/empty files
    valid_files = []
    for file in files:
        if not file:
            continue
        if isinstance(file, str) and file.strip() == "":
            continue
        if hasattr(file, 'filename') and not getattr(file, 'filename', None):
            continue
        valid_files.append(file)

    if not valid_files:
        return []

    # GCP upload only.
    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Install it and try again.")

    if not settings.gcp_service_account_file:
        raise RuntimeError("GCP service account file not configured. Set GCP_SERVICE_ACCOUNT_FILE in .env")

    if not (bucket_name or os.environ.get("GCP_BUCKET_NAME") or settings.gcp_bucket_name):
        raise RuntimeError("GCP bucket not configured. Set GCP_BUCKET_NAME in .env or pass bucket_name")

    try:
        bucket = get_storage_bucket(bucket_name)
        uploaded_urls = []

        for i, file in enumerate(valid_files):
            # Create unique path for each file
            if "{i}" in base_path:
                path = base_path.format(i=i)
            else:
                # If no placeholder, append index
                path = f"{base_path}_{i}"

            normalized = path.lstrip("/")
            blob = bucket.blob(normalized)
            
            # Resize image
            resized_file = resize_image(file.file)
            blob.upload_from_file(resized_file, rewind=True)

            # Construct public URL
            public_url = f"https://storage.googleapis.com/{bucket.name}/{blob.name}"
            uploaded_urls.append(public_url)

        return uploaded_urls
    except Exception as e:
        raise RuntimeError(f"Batch GCP upload failed: {e}")


def get_location_from_pincode(pincode: str) -> Optional[dict]:
    """
    Get district and state_name for a given pincode.
    
    Returns a dict with 'district' and 'state_name' keys, or None if not found.
    """
    db = SessionLocal()
    try:
        pincode_data = db.query(Pincode).filter(Pincode.pincode == pincode).first()
        if pincode_data:
            return {
                "district": pincode_data.district,
                "state_name": pincode_data.state_name
            }
        return None
    finally:
        db.close()


def delete_from_gcp(blob_name: str, bucket_name: Optional[str] = None) -> bool:
    """
    Delete a blob from GCP storage.

    Args:
        blob_name: The name of the blob to delete (without bucket prefix)
        bucket_name: Optional bucket name override

    Returns:
        True if deleted successfully, False otherwise
    """
    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Install it and try again.")

    env_bucket = os.environ.get("GCP_BUCKET_NAME") or settings.gcp_bucket_name
    if bucket_name is None:
        if not env_bucket:
            raise RuntimeError("GCP bucket name not provided. Set GCP_BUCKET_NAME in your .env or settings")
        bucket_name = env_bucket

    if not settings.gcp_service_account_file:
        raise RuntimeError("GCP service account file not configured. Set GCP_SERVICE_ACCOUNT_FILE in .env")

    try:
        client = storage.Client.from_service_account_json(settings.gcp_service_account_file)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if blob.exists():
            blob.delete()
            return True
        return False
    except Exception as e:
        raise RuntimeError(f"GCP delete failed: {e}")


def delete_images_from_gcp(urls: list[str], bucket_name: Optional[str] = None) -> int:
    """
    Delete multiple images from GCP based on their public URLs.

    Args:
        urls: List of public URLs
        bucket_name: Optional bucket name override

    Returns:
        Number of successfully deleted images
    """
    if not urls:
        return 0

    env_bucket = os.environ.get("GCP_BUCKET_NAME") or settings.gcp_bucket_name
    if bucket_name is None:
        bucket_name = env_bucket

    deleted_count = 0
    for url in urls:
        # Extract blob name from URL
        # URL format: https://storage.googleapis.com/{bucket}/{blob_name}
        try:
            parts = url.split('/')
            if len(parts) >= 5 and parts[2] == 'storage.googleapis.com':
                blob_name = '/'.join(parts[4:])
                if delete_from_gcp(blob_name, bucket_name):
                    deleted_count += 1
        except Exception:
            continue  # Skip invalid URLs
    return deleted_count

try:
    from PIL import Image
except ImportError:
    Image = None

def resize_image(image_file, max_size=(1920, 1080)):
    """
    Resize image to fit within max_size while maintaining aspect ratio.
    Target is around 1080p.

    Args:
        image_file: File-like object
        max_size: Tuple of (width, height)

    Returns:
        BytesIO object with resized image
    """
    if Image is None:
        raise RuntimeError("Pillow not installed. Install it to resize images.")

    try:
        image = Image.open(image_file)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        from io import BytesIO
        output = BytesIO()
        image.save(output, format=image.format or 'JPEG', quality=85)
        output.seek(0)
        return output
    except Exception as e:
        raise RuntimeError(f"Image resize failed: {e}")
