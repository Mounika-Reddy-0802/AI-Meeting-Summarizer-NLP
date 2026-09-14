# W1 — Lahari — SAMSum fine-tune

Branch `week1-lahari-samsum-finetune` · PROJECT_PLAN.md §4 dataset verification and §5 Lahari tasks 1–8

## What I built

- **Dataset check (Day 1)** — `data/README.md`: every source loaded or downloaded, with sizes, licences
  and citations. Surprises: `Samsung/samsum` is gone from the Hub (we use `knkarthick/samsum`,
  14,731 / 818 / 819); `knkarthick/AMI` is gated (accept the terms before Week 2); MRDA on the Hub is a
  loading script only, but its CSVs download directly from the SILICONE GitHub repo (for Krishna, W2).
- **Data** — `ml/data/prepare.py`: `load_samsum()` returns `id, dialogue, summary` with one
  `Speaker: text` line per turn; `load_dialogsum()` and `load_ami()` are Week 2 stubs.
  `ml/data/format.py`: turn parsing, speaker tags on/off, um/uh filler removal, and the input prefix
  `summarize:` (Week 3 adds `summarize decisions:` etc. to the same function).
- **Training** — `ml/train.py`: Seq2SeqTrainer on `google/flan-t5-base`, 1024 input / 128 target
  tokens, 3 epochs, ROUGE on 300 validation dialogues each epoch, best epoch kept by ROUGE-L. `--lora`
  (r=16 on q/v, merged before saving), `--push_to_hub` (private repo, every epoch plus
  `last-checkpoint/`), `--resume_from_checkpoint last|hub|<folder>`, ablation flags
  `--no_speaker_tags` / `--remove_fillers`. Writes `run_info.json` (parameter counts, GPU, runtime,
  best validation scores, full log history).
- **Kaggle** — `ml/kaggle/train_samsum.ipynb` (outputs stripped): clone → install → train → score
  zero-shot and fine-tuned on the test set → collect files. Step-by-step in `ml/README.md`.
- **Baseline + evaluation** — `ml/extractive_baseline.py` (TextRank over turns, k=2);
  `ml/evaluate.py --system extractive|zero-shot|finetuned` computes ROUGE-1/2/L/Lsum and BERTScore F1,
  replaces its row in `benchmarks/raw/results.csv`, saves per-example predictions, and regenerates
  `benchmarks/summarization_results.md` from the csv.
- **Backend** — `backend/app/services/summarize.py` v1: loads the checkpoint from
  `MODEL_DIR/summarizer`, builds the same `summarize:` + `Speaker: text` input from diarised segments,
  single pass (beam 4, 1024-token truncation until Week 2 chunking). Without a checkpoint it keeps the
  old first-3-segments behaviour. Same `summarize(segments) -> SummaryResult` interface as Mounika's
  stub.

## How to run

```powershell
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r ml/requirements.txt
pytest ml/tests                                   # 9 tests
python ml/data/prepare.py --dataset samsum
python ml/evaluate.py --system extractive         # ~10 s + BERTScore
```

Training and the two generative rows: `ml/README.md` → "Kaggle run".

## Numbers

From `benchmarks/raw/results.csv` (SAMSum test, 819 dialogues):

| System | ROUGE-1 | ROUGE-2 | ROUGE-L | BERTScore F1 | Where it ran |
|--------|--------:|--------:|--------:|-------------:|--------------|
| extractive (TextRank, k=2) | 0.2903 | 0.0830 | 0.2313 | 0.8628 | laptop CPU |
| zero-shot flan-t5-base | pending | | | | Kaggle |
| fine-tuned flan-t5-base (SAMSum) | pending | | | | Kaggle |

**The Kaggle run has not happened yet**, so there is no checkpoint and no fine-tuned number. The
notebook, the Hub repo name (`<hf-user>/flan-t5-base-samsum`) and the steps are ready; after the run,
the notebook version link, GPU hours and the two rows go here and into the csv.

## Problems and decisions

- **Zero-shot on CPU is too slow for the full test set.** A timing check on 8–32 test dialogues
  (`--max_samples`, not saved) took roughly 20 s per dialogue with beam 4 on this laptop, about 4–5 h
  for all 819, so the zero-shot row runs on Kaggle together with the fine-tuned one (same GPU, same
  settings). This is also an early warning for the "runs on a laptop" claim — the Week 4 int8 and
  latency work matters.
- **fp32 on Kaggle.** T5-family models are known to produce NaN loss in fp16 and T4/P100 have no bf16,
  so `--precision auto` picks fp32 there. If the run is too slow we can try `--precision fp16` and watch
  the loss.
- **TextRank picked attachment placeholders.** SAMSum writes images/GIFs as `<file_gif>`; identical
  placeholder turns scored as highly similar and were selected. Placeholders are now ignored and the
  row above was recomputed after the fix.
- `train.py` was smoke-tested on CPU with `flan-t5-small`, 32 examples, 4–8 steps (full, LoRA, resume)
  to check the code path only; nothing from it is reported.
- `summarize.py` was checked against Mounika's backend branch: her 15 tests pass with it, ruff is clean,
  and it loads a checkpoint folder and generates. Merging will conflict with her stub at the same path —
  take this version.

## Next

- Run `train_samsum.ipynb` on Kaggle; commit the two rows, `run_info.json`, notebook link and time.
- Share `<hf-user>/flan-t5-base-samsum` with the team (read token) so Gate 1 can load it offline.
- Week 2 (`week2-lahari-ami-chunking`): `load_dialogsum`, `load_ami`, `ami_sections.py`, chunking, LoRA vs full.
