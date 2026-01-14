import os


class Settings:
    database_url: str = os.environ.get("DATABASE_URL", "postgresql://ledger:ledger_secret@db:5432/ledger")
    api_key: str = os.environ.get("API_KEY", "dev-api-key-change-me")
    archive_path: str = os.environ.get("ARCHIVE_PATH", "/archive")


def get_settings() -> Settings:
    return Settings()