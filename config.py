
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-only-change-this-key"
    )

    DATABASE_PATH = BASE_DIR / "database" / "securelens.db"

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    JSON_SORT_KEYS = False
