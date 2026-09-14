"""Application settings, read from environment variables and backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Runtime configuration. Relative paths are resolved against backend/."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
        env_ignore_empty=True,
        protected_namespaces=(),
    )

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    database_url: str = f"sqlite:///{(REPO_DIR / 'data' / 'app.db').as_posix()}"
    data_dir: Path = REPO_DIR / "data"
    model_dir: Path = REPO_DIR / "models"
    whisper_size: str = "small"
    max_audio_minutes: int = 60

    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("data_dir", "model_dir")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        """Make relative paths independent of the working directory."""
        return value if value.is_absolute() else (BACKEND_DIR / value).resolve()

    @property
    def audio_dir(self) -> Path:
        """Converted uploads, named by content hash."""
        return self.data_dir / "audio"

    @property
    def transcripts_dir(self) -> Path:
        """Cached ASR + diarisation JSON, keyed by file hash."""
        return self.data_dir / "transcripts"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
