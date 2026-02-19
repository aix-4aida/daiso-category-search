import sys
import os
import traceback

sys.path.append(os.getcwd())
print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    from backend.database.database import init_database
    print("Import successful")
    init_database()
    print("Init successful")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
