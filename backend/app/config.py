"""Application settings, read from environment variables and backend/.env."""

import os
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
    max_upload_mb: int = 500
    # drop um/uh-style fillers from stored segments; backchannels are always kept
    filler_cleanup: bool = False

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


def apply_model_env(settings: Settings, offline: bool = True) -> None:
    """Point every model library's cache at MODEL_DIR; with offline=True forbid downloads.

    Must run before faster-whisper, pyannote, transformers or sentence-transformers are imported.
    """
    os.environ["HF_HOME"] = str(settings.model_dir / "huggingface")
    os.environ["PYANNOTE_CACHE"] = str(settings.model_dir / "pyannote")
    os.environ["TORCH_HOME"] = str(settings.model_dir / "torch")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    flag = "1" if offline else "0"
    os.environ["HF_HUB_OFFLINE"] = flag
    os.environ["TRANSFORMERS_OFFLINE"] = flag
