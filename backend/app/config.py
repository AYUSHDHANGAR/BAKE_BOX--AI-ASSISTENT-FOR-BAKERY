"""
Configuration utilities for BAKEBOX backend.
Loads environment variables from RAG.env.txt (located at project root) using python-dotenv.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Locate environment files at project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load standard .env first
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Also load RAG.env.txt if present
ENV_PATH = BASE_DIR / "RAG.env.txt"
if ENV_PATH.is_file():
    load_dotenv(dotenv_path=ENV_PATH)
    # Parse custom 'KEY : VALUE' format in RAG.env.txt if any
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    k, v = k.strip(), v.strip()
                    if k and v and k not in os.environ:
                        os.environ[k] = v
                        if k == "GEMINI_API" and "GEMINI_API_KEY" not in os.environ:
                            os.environ["GEMINI_API_KEY"] = v
    except Exception:
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