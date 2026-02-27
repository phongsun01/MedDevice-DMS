"""
MedDevice DMS - Configuration (Pydantic Settings)
"""
from pydantic_settings import BaseSettings
import json
from pathlib import Path



class Settings(BaseSettings):
    """All env vars loaded from .env automatically."""

    # SurrealDB
    SURREAL_URL: str = "ws://localhost:8000/rpc"
    SURREAL_USER: str = "root"
    SURREAL_PASS: str = "root"
    SURREAL_NS: str = "meddevice"
    SURREAL_DB: str = "dms"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ALLOWED_USERS: str = ""  # comma-separated IDs
    WEBHOOK_URL: str = ""

    # Gemini AI
    GEMINI_API_KEY: str = ""

    # Outline Wiki
    OUTLINE_API_URL: str = "http://localhost:3000/api"
    OUTLINE_API_TOKEN: str = ""

    # Storage
    STORAGE_BASE_PATH: str = "D:\\MedicalData"

    # Agent mode: "A" = gemini-cli agentic, "B" = standalone Gemini API, "C" = IDE queue
    AGENT_MODE: str = "B"

    @property
    def data_naming(self) -> dict:
        """Load naming prefixes and suffixes from config/data_naming.json."""
        config_path = Path(__file__).parent / "config" / "data_naming.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"prefixes": {}, "suffixes": {}}

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def allowed_user_ids(self) -> list[int]:
        """Parse comma-separated user IDs into a list of ints."""
        if not self.TELEGRAM_ALLOWED_USERS:
            return []
        return [int(uid.strip()) for uid in self.TELEGRAM_ALLOWED_USERS.split(",") if uid.strip()]


settings = Settings()
