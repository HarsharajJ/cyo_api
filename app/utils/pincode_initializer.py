import pandas as pd
from sqlalchemy import inspect, select
from app.database import engine, SessionLocal
from app.models.pincode import Pincode
import os

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
                        zipcode=str(row['Zipcode']),
                        district=row['District'],
                        state_name=row['StateName']
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
