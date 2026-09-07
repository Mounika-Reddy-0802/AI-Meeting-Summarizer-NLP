# data/

Gitignored working directory - nothing here is committed except this file.

- `data/audio/` - uploaded meeting audio saved by the backend.
- `data/transcripts/` - cached Deepgram JSON so a file is never transcribed twice.
- Datasets (SAMSum, DialogSum, AMI) are downloaded by `ml/data/prepare.py`; see `ml/README.md`.
