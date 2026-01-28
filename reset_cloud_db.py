import sys
from sqlalchemy import text
from app.database import engine
from app.db.init_db import drop_all_tables
from app.config import settings

def reset_db():
    print(f"⚠️  DANGER: You are about to DESTROY ALL DATA in: {settings.DATABASE_URL.split('@')[-1]}")
    confirm = input("Are you absolutely sure? Type 'DELETE_CLOUD_DATA' to confirm: ")
    
    if confirm != 'DELETE_CLOUD_DATA':
        print("❌ Operation cancelled.")
        return

    # 1. Drop all tables using metadata
    print("\n💥 Dropping application tables...")
    drop_all_tables()
    
    # 2. Drop alembic_version table manually if it exists (to reset migration history)
    print("🧹 Cleaning up alembic history...")
    with engine.connect() as connection:
        try:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
            connection.commit()
            print("✅ Alembic version table dropped.")
        except Exception as e:
            print(f"⚠️  Could not drop alembic_version (might not exist): {e}")

    print("\n✨ Database is now empty and ready for fresh initialization.")

if __name__ == "__main__":
    reset_db()
