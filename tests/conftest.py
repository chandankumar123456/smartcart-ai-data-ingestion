import os

# Set the in-memory database URL before any module-level imports trigger
# database initialization, ensuring tests never touch the real database file.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
