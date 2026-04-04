"""One-time database initialization script for Analytic."""
import os
import sys
from db import init_db, is_db_available

if __name__ == "__main__":
    print("Initializing Analytic PostgreSQL database...")

    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL not set. Export it and try again:")
        print("   export DATABASE_URL=postgresql://...")
        sys.exit(1)

    init_db()

    if is_db_available():
        print("Database initialized successfully!")
        print("   Tables created: uploads, db_sessions, dismissals")
        sys.exit(0)
    else:
        print("Database initialization failed. Check logs above.")
        sys.exit(1)
