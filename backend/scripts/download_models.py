"""Download every model the backend needs into MODEL_DIR. Run once with network access.

    python scripts/download_models.py

After this the app loads everything from MODEL_DIR with downloads disabled. HF_TOKEN in
backend/.env is needed only for pyannote, whose model terms must be accepted on the Hub first.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic_settings import BaseSettings, SettingsConfigDict  # noqa: E402

from app.config import BACKEND_DIR, apply_model_env, get_settings  # noqa: E402

PYANNOTE_PIPELINE = "pyannote/speaker-diarization-3.1"
PYANNOTE_TERMS = [
    "https://huggingface.co/pyannote/speaker-diarization-3.1",
    "https://huggingface.co/pyannote/segmentation-3.0",
]
HUB_MODELS = ["sentence-transformers/all-MiniLM-L6-v2", "cross-encoder/nli-deberta-v3-base"]
# only the PyTorch weights are used; skip the other runtimes' copies
SKIP_FILES = [
    "onnx/*",
    "openvino/*",
    "*.onnx",
    "*.h5",
    "*.msgpack",
    "*.ot",
    "tf_model*",
    "flax_model*",
]


class DownloadSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", extra="ignore", env_ignore_empty=True
    )

    hf_token: str | None = None


def folder_size_mb(path: Path) -> float:
    return (
        sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6 if path.exists() else 0
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-pyannote", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    apply_model_env(settings, offline=False)
    print(f"MODEL_DIR = {settings.model_dir}")

    from faster_whisper import download_model
    from huggingface_hub import snapshot_download

    print(f"[1/4] faster-whisper {settings.whisper_size}")
    download_model(settings.whisper_size)

    for i, repo_id in enumerate(HUB_MODELS, start=2):
        print(f"[{i}/4] {repo_id}")
        snapshot_download(repo_id, ignore_patterns=SKIP_FILES)

    failed = False
    if args.skip_pyannote:
        print("[4/4] pyannote skipped")
    else:
        print(f"[4/4] {PYANNOTE_PIPELINE}")
        token = DownloadSettings().hf_token
        if not token:
            print(
                "HF_TOKEN is missing. Create a read token at https://huggingface.co/settings/tokens,\n"
                "put it in backend/.env as HF_TOKEN=..., accept the terms on:\n  "
                + "\n  ".join(PYANNOTE_TERMS)
            )
            failed = True
        else:
            from pyannote.audio import Pipeline

            if Pipeline.from_pretrained(PYANNOTE_PIPELINE, use_auth_token=token) is None:
                print(
                    "pyannote download refused - accept the terms on:\n  "
                    + "\n  ".join(PYANNOTE_TERMS)
                )
                failed = True

    print(f"MODEL_DIR size: {folder_size_mb(settings.model_dir):.0f} MB")
    print(
        "Some models are missing." if failed else "All models downloaded. The app now runs offline."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
