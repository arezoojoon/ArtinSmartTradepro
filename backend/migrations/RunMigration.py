import sys
import os
from sqlalchemy import text

# Add parent dir to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db

def run_migration():
    print("🔄 Starting Migration: add_brain_columns.sql")
    try:
        db = next(get_db())
        
        # Read SQL file
        migration_file = os.path.join(os.path.dirname(__file__), 'add_brain_columns.sql')
        with open(migration_file, 'r') as f:
            sql_content = f.read()
            
        # Execute
        # We split by semicolon to be safe, though text() might handle blocks
        statements = sql_content.split(';')
        for stmt in statements:
            if stmt.strip():
                print(f"Executing: {stmt[:50]}...")
                db.execute(text(stmt))
        
        db.commit()
        print("✅ Migration applied successfully.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
