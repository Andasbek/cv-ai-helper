from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./cv_helper.db"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 20
    backend_url: str = "http://localhost:8000"


settings = Settings()
