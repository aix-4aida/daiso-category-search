"""
Sync Script for Daiso Search MVP
SQLite (products.db) -> ChromaDB
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent
sys.path.append(str(root))

from backend.database.database import sync_to_chroma, init_database

if __name__ == "__main__":
    print("🚀 Starting Database Sync for MVP...")
    init_database()
    sync_to_chroma()
    print("✨ Sync Complete!")
