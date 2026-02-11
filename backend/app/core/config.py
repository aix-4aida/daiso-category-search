
import yaml
from pathlib import Path
from functools import lru_cache

class Settings:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        # Assuming config.yaml is in backend/ directory
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "backend/config.yaml"
        if not config_path.exists():
            # Fallback to backend/api.py location style logic if needed
            config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            print(f"⚠️ Warning: Config file not found at {config_path}")

    @property
    def stt_config(self):
        return self.config.get("stt", {})

    @property
    def quality_gate_config(self):
        return self.config.get("quality_gate", {})
    
    @property
    def policy_gate_config(self):
        return self.config.get("policy_gate", {})

@lru_cache()
def get_settings():
    return Settings()
