import os
from sqlalchemy import text, inspect
from app.database import engine, Base
import app.models  # Import models to ensure Base has the metadata

def verify_connection():
    print("Checking database connection...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                print("[OK] Connection successful!")
                return True
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

def verify_tables():
    print("\nVerifying tables...")
    # Create tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables created/verified via Base.metadata.create_all")
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        return

    # Inspect database to see what tables actually exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Tables found in database: {existing_tables}")

    expected_tables = ["projects", "artifacts", "doc_versions", "pipeline_runs"]
    for table in expected_tables:
        if table in existing_tables:
            print(f"[OK] Table '{table}' exists.")
        else:
            print(f"[ERROR] Table '{table}' is MISSING.")

if __name__ == "__main__":
    if verify_connection():
        verify_tables()
    else:
        print("\nCould not verify tables because connection failed.")
