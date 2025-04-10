import json
from pathlib import Path

class ConfigService:
    def __init__(self):
        self.config_file = Path("config/config.json")
        self.config_file.parent.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self._save({"connection_endpoint": "", "gemini_api_key": ""})

    def _save(self, config: dict):
        self.config_file.write_text(json.dumps(config, indent=2))

    def _load(self) -> dict:
        return json.loads(self.config_file.read_text())

    def get_connection_endpoint(self) -> str:
        return self._load().get("connection_endpoint", "")

    def get_gemini_api_key(self) -> str:
        return self._load().get("gemini_api_key", "")

    def update_connection_settings(self, endpoint: str, gemini_api_key: str):
        config = self._load()
        config["connection_endpoint"] = endpoint
        config["gemini_api_key"] = gemini_api_key
        self._save(config)
