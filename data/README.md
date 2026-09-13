# data/

Gitignored. Nothing in this folder is committed except this file.

- `data/audio/` - uploaded recordings, converted to 16 kHz mono wav, named by content hash.
- `data/transcripts/` - cached local ASR + diarisation JSON so a file is never transcribed twice.
- `data/datasets/` - downloaded training data. How to fetch each one (fill in on Day 1, Lahari):
  - SAMSum — `datasets.load_dataset("Samsung/samsum")`
  - DialogSum — `datasets.load_dataset("knkarthick/dialogsum")`
  - AMI plain summaries — `datasets.load_dataset("knkarthick/AMI")`
  - AMI manual annotations v1.6.2 (NXT XML, `abstractive/*.abssumm.xml` for sections) — from the AMI corpus site
  - QMSum — clone github.com/Yale-LILY/QMSum
  - MRDA — `datasets.load_dataset("silicone", "mrda")`
- Licences and citation lines for each dataset go here once verified.
