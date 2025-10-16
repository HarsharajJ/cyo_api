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

    Reads bucket name from GCS_BUCKET_NAME env var if not supplied.
    Raises RuntimeError on failure. Returns the bucket name on success.
    """
    # Try OS env first, then pydantic settings (which reads .env)
    env_bucket = os.environ.get("GCS_BUCKET_NAME") or settings.gcs_bucket_name
    if bucket_name is None:
        if not env_bucket:
            raise RuntimeError("GCS bucket name not provided. Set GCS_BUCKET_NAME in your .env or settings")
        bucket_name = env_bucket

    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Add it to requirements.txt and install.")

    # emulator host is read by the client library from env var STORAGE_EMULATOR_HOST
    # prefer OS env var, otherwise use settings
    emulator_host = os.environ.get("STORAGE_EMULATOR_HOST") or settings.storage_emulator_host
    if emulator_host:
        os.environ["STORAGE_EMULATOR_HOST"] = emulator_host

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    try:
        if not bucket.exists():
            bucket.create()
    except Exception as e:
        raise RuntimeError(f"Unable to access/create bucket '{bucket_name}': {e}")

    return bucket_name


def get_storage_bucket(bucket_name: Optional[str] = None):
    """Return a google.cloud.storage.Bucket instance for the configured bucket."""
    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Add it to requirements.txt and install.")

    env_bucket = os.environ.get("GCS_BUCKET_NAME") or settings.gcs_bucket_name
    if bucket_name is None:
        if not env_bucket:
            raise RuntimeError("GCS bucket name not provided. Set GCS_BUCKET_NAME in your .env or settings")
        bucket_name = env_bucket

    # ensure emulator host is set for the client if present in settings
    emulator_host = os.environ.get("STORAGE_EMULATOR_HOST") or settings.storage_emulator_host
    if emulator_host:
        os.environ["STORAGE_EMULATOR_HOST"] = emulator_host

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        bucket.create()
    return bucket


def save_image(file, path: str, bucket_name: Optional[str] = None) -> Optional[str]:
    """
    Save an UploadFile to cloud storage (if configured) or to local `uploads/`.

    Returns the URL/path to store in DB, or None if no file was provided.
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

    # Cloud upload only. If storage not configured or upload fails, raise.
    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Install it and try again.")

    if not (bucket_name or os.environ.get("GCS_BUCKET_NAME") or settings.gcs_bucket_name):
        raise RuntimeError("GCS bucket not configured. Set GCS_BUCKET_NAME in .env or pass bucket_name")

    # Ensure emulator host from settings is available to client
    emulator_host = os.environ.get("STORAGE_EMULATOR_HOST") or settings.storage_emulator_host
    if emulator_host:
        os.environ["STORAGE_EMULATOR_HOST"] = emulator_host

    try:
        bucket = get_storage_bucket(bucket_name)
        blob = bucket.blob(normalized)
        file.file.seek(0)
        blob.upload_from_file(file.file, rewind=True)
        emulator = os.environ.get("STORAGE_EMULATOR_HOST")
        if emulator:
            return f"{emulator}/storage/v1/b/{bucket.name}/o/{blob.name}?alt=media"
        return blob.public_url
    except Exception as e:
        raise RuntimeError(f"Cloud upload failed: {e}")


def save_images(files, base_path: str, bucket_name: Optional[str] = None) -> list[str]:
    """
    Save multiple UploadFiles to cloud storage efficiently.

    Args:
        files: List of UploadFile objects or single UploadFile
        base_path: Base path template (should include placeholders for indexing)
        bucket_name: Optional bucket name override

    Returns:
        List of URLs/paths for the uploaded files
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

    # Cloud upload only. If storage not configured or upload fails, raise.
    if storage is None:
        raise RuntimeError("google-cloud-storage not installed. Install it and try again.")

    if not (bucket_name or os.environ.get("GCS_BUCKET_NAME") or settings.gcs_bucket_name):
        raise RuntimeError("GCS bucket not configured. Set GCS_BUCKET_NAME in .env or pass bucket_name")

    # Ensure emulator host from settings is available to client
    emulator_host = os.environ.get("STORAGE_EMULATOR_HOST") or settings.storage_emulator_host
    if emulator_host:
        os.environ["STORAGE_EMULATOR_HOST"] = emulator_host

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
            file.file.seek(0)
            blob.upload_from_file(file.file, rewind=True)

            emulator = os.environ.get("STORAGE_EMULATOR_HOST")
            if emulator:
                url = f"{emulator}/storage/v1/b/{bucket.name}/o/{blob.name}?alt=media"
            else:
                url = blob.public_url
            uploaded_urls.append(url)

        return uploaded_urls
    except Exception as e:
        raise RuntimeError(f"Batch cloud upload failed: {e}")


