"""
Backend test conftest — loads .env before the FastAPI app is imported.
"""
import os
import sys
from pathlib import Path

# Ensure backend/ is on the path (for routers, models, services, …)
BACKEND_DIR = Path(__file__).parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Mark this as a test environment so middleware (rate limiter, etc.) can adapt
os.environ.setdefault("APP_ENV", "test")

# Load .env from project root so JWT_SECRET_KEY etc. are available
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR.parent / ".env")
