"""
Configuration utilities for BAKEBOX backend.
Loads environment variables from RAG.env.txt (located at project root) using python-dotenv.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Locate the .env file – default to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend directory
ENV_PATH = BASE_DIR / "RAG.env.txt"

if ENV_PATH.is_file():
    # The RAG.env.txt may contain lines like KEY=VALUE; load them
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # Fallback: rely on OS environment variables
    pass

# Export commonly used settings
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "50000")
DB_DATABASE = os.getenv("DB_DATABASE", "IBMDB201")
DB_USER = os.getenv("DB_USER", "dbayush")
DB_PASSWORD = os.getenv("DB_PASSWORD", "8844")

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_secret")
JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))