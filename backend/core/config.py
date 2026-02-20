
import yaml
from pathlib import Path

# Prioritize backend/config.yaml, fallback to root/config.yaml
BACKEND_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BACKEND_DIR / "config.yaml"

if not CONFIG_PATH.exists():
    CONFIG_PATH = BACKEND_DIR.parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
