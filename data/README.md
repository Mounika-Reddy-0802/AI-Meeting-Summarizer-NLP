# data/

Gitignored. Nothing in this folder is committed except this file.

- `data/audio/` - uploaded recordings, converted to 16 kHz mono wav, named by content hash.
- `data/transcripts/` - cached local ASR + diarisation JSON so a file is never transcribed twice.
- `data/datasets/` - downloaded training data (the Hugging Face cache is used by default).

## Datasets — Day 1 verification (Lahari, 14 Sep 2026)

| Dataset | Status | How to get it | Size | Licence |
|---------|--------|---------------|------|---------|
| SAMSum | **works, new repo id** | `load_dataset("knkarthick/samsum")` — `Samsung/samsum` no longer exists on the Hub | 14,731 / 818 / 819 (train / validation / test; the paper reports 14,732 train), columns `id, dialogue, summary`; no empty rows | CC BY-NC-ND 4.0 |
| DialogSum | works | `load_dataset("knkarthick/dialogsum")` | 12,460 / 500 / 1,500, columns `id, dialogue, summary, topic` | CC BY-NC-SA 4.0 |
| AMI plain summaries | **gated** | `load_dataset("knkarthick/AMI")` after accepting the terms on https://huggingface.co/datasets/knkarthick/AMI while logged in (token needed on Kaggle) | not checked (gated) | CC BY 4.0 |
| AMI manual annotations v1.6.2 | works | https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip (22 MB, NXT XML; sections in `abstractive/*.abssumm.xml`) | 22 MB zip | CC BY 4.0 |
| QMSum | works | `git clone https://github.com/Yale-LILY/QMSum` | AMI + ICSI + parliamentary meetings | see the repo; AMI/ICSI parts follow the corpus licences |
| MRDA (dialogue acts) | **script-only on the Hub** | `eusip/silicone` is a loading script, which `datasets` 4 no longer runs. The same CSVs download directly: `https://raw.githubusercontent.com/eusip/SILICONE-benchmark/main/mrda/{train,dev,test}.csv` (columns `Utterance_ID, Dialogue_Act, Channel_ID, Speaker, Dialogue_ID, Utterance`) | 8.0 / 0.9 / 1.4 MB | CC BY-SA 4.0 (SILICONE) |

Notes for later weeks:

- **Leakage rule:** AMI test meeting ids must be held out of every training stage, including QMSum
  augmentation (filter by meeting id in `ml/data/prepare.py`).
- SAMSum and DialogSum are non-commercial licences: fine for this project and the report, but the
  published model card must say the checkpoint was trained on NC data.
- `ml/requirements.txt` pins `datasets<4` so script-based datasets still load if we need one.

## Citations

- SAMSum — Gliwa et al., 2019. *SAMSum Corpus: A Human-annotated Dialogue Dataset for Abstractive Summarization.* Workshop on New Frontiers in Summarization.
- DialogSum — Chen et al., 2021. *DialogSum: A Real-Life Scenario Dialogue Summarization Dataset.* Findings of ACL.
- AMI — Carletta et al., 2005. *The AMI Meeting Corpus: A Pre-announcement.* MLMI.
- QMSum — Zhong et al., 2021. *QMSum: A New Benchmark for Query-based Multi-domain Meeting Summarization.* NAACL.
- MRDA — Shriberg et al., 2004. *The ICSI Meeting Recorder Dialog Act (MRDA) Corpus.* SIGDIAL. SILICONE — Chapuis et al., 2020, Findings of EMNLP.
