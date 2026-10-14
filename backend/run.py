"""
Entry point to run TERRA FastAPI backend server.
Usage: python run.py
"""

import uvicorn
import os
import sys

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    backend_app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[backend_app_dir],
        reload_excludes=["*.db", "*.db-journal", "*.db-wal", "terra.db*", "*.pyc", "*__pycache__*"]
    )
