# W1 · Lahari — dataset verification, SAMSum fine-tune setup and baselines

Branch `week1-lahari-samsum-finetune` · PROJECT_PLAN.md §4 (Day 1 dataset check) and §5 Lahari tasks 1–8

## What I built

**Dataset verification (Day 1)** — `data/README.md`. Every source loaded or downloaded, with split
sizes, licences and citations. Three surprises the plan did not expect:
- `Samsung/samsum` **no longer exists on the Hub.** We use `knkarthick/samsum`, which has
  14,731 / 818 / 819 dialogues (the paper reports 14,732 train) and no empty rows.
- `knkarthick/AMI` is **gated** — the terms must be accepted on the Hub before Week 2.
- MRDA on the Hub (`eusip/silicone`) is **a loading script only**, which `datasets` 4 no longer runs;
  the same CSVs download directly from the SILICONE GitHub repo. Passed to Krishna for Week 2.

**Data** — `ml/data/prepare.py`: `load_samsum()` returns `id, dialogue, summary` with one
`Speaker: text` line per turn; `load_dialogsum()` and `load_ami()` are Week 2 stubs.
`ml/data/format.py`: turn parsing, speaker tags on/off, um/uh filler removal, and the input prefix
`summarize:`. Week 3 adds `summarize decisions:` / `actions:` / `problems:` to the same function, so
one model serves every section.

**Training** — `ml/train.py`: Seq2SeqTrainer on `google/flan-t5-base`, 1024 input / 128 target tokens,
3 epochs, ROUGE on 300 validation dialogues each epoch, best epoch kept by ROUGE-L.
- `--lora` (r=16 on q/v), merged into the base weights before saving, so the backend always loads a
  plain seq2seq model.
- `--push_to_hub` to a private repo, every epoch plus `last-checkpoint/`;
  `--resume_from_checkpoint last|hub|<folder>` continues after a dead Kaggle session.
- Ablation flags `--no_speaker_tags` / `--remove_fillers` exist now, so Week 2's ablations are
  flag changes rather than new code.
- Writes `run_info.json`: parameter counts, GPU, runtime, best validation scores, full log history.

**Kaggle notebook** — `ml/kaggle/train_samsum.ipynb` (outputs stripped): clone → install → train →
score zero-shot and fine-tuned on the test set on the same GPU → collect the files to commit.
Exact click-by-click steps in `ml/README.md`.

**Baseline and evaluation** — `ml/extractive_baseline.py` (TextRank over turns, k=2);
`ml/evaluate.py --system extractive|zero-shot|finetuned` computes ROUGE-1/2/L/Lsum and BERTScore F1,
replaces its own row in `benchmarks/raw/results.csv`, saves per-example predictions, and regenerates
`benchmarks/summarization_results.md` from the csv — so the table can never hold a number the csv does
not. ROUGE is a plain mean, not `rouge_score`'s bootstrap estimate, so reruns give identical numbers.

**Backend** — `backend/app/services/summarize.py` v1: loads the checkpoint from `MODEL_DIR/summarizer`,
builds the same `summarize:` + `Speaker: text` input from diarised segments, single pass (beam 4,
1024-token truncation until Week 2's chunking). Without a checkpoint it keeps the old
first-three-segments behaviour, so the pipeline and its tests still run. Same
`summarize(segments) -> SummaryResult` interface as Mounika's stub.

## How to run / verify

```powershell
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r ml/requirements.txt
pytest ml/tests                                   # 9 tests
python ml/data/prepare.py --dataset samsum        # split sizes + one example
python ml/evaluate.py --system extractive         # ~10 s, then BERTScore
python ml/evaluate.py --table                     # rebuild the markdown table from the csv
```

Training and the two generative rows: `ml/README.md` → "Kaggle run".

## Numbers

From `benchmarks/raw/results.csv` — SAMSum test, 819 dialogues:

| System | ROUGE-1 | ROUGE-2 | ROUGE-L | BERTScore F1 | Where it ran |
|---|---:|---:|---:|---:|---|
| extractive (TextRank, k=2) | 0.2903 | 0.0830 | 0.2313 | 0.8628 | laptop CPU |
| zero-shot flan-t5-base | pending | | | | Kaggle GPU |
| fine-tuned flan-t5-base (SAMSum) | pending | | | | Kaggle GPU |

| Item | Value |
|---|---|
| SAMSum splits loaded | 14,731 / 818 / 819 |
| Mean dialogue length (test) | 96 words, max 516 |
| Datasets verified | 6 (SAMSum, DialogSum, AMI plain, AMI annotations, QMSum, MRDA) |
| Unit tests | 9 |

## Status — verified by running, not by inspection

- ✅ **All six dataset sources checked** and recorded in `data/README.md`.
- ✅ **`train.py` smoke-tested on CPU** with `flan-t5-small`, 32 examples, 4–8 steps — full fine-tune,
  LoRA (0.89 % of parameters trainable, merged cleanly) and resume from the last checkpoint. This checks
  the code path only; nothing from it is reported.
- ✅ **TextRank row measured** on all 819 test dialogues.
- ✅ **`summarize.py` checked against Mounika's backend:** her 15 tests pass with it, ruff is clean, and
  it loads a checkpoint folder and generates.
- ⬜ **The Kaggle run has not happened**, so there is no checkpoint and no fine-tuned number. This is the
  main Gate 1 blocker and it is mine. The notebook, the Hub repo name
  (`<hf-user>/flan-t5-base-samsum`) and the steps are ready.
- ⬜ The zero-shot row moved to the Kaggle notebook — see below.
- ⬜ PR to `dev` not opened yet.

### Problems and decisions

- **Zero-shot on CPU is too slow for the full test set.** A timing check on 8–32 test dialogues
  (`--max_samples`, not saved) took roughly 20 s per dialogue with beam 4 on this laptop — 4–5 hours
  for all 819. The zero-shot row therefore runs on Kaggle beside the fine-tuned one, on the same GPU
  with the same settings. It is also an early warning for the "runs on a laptop" claim, which makes
  Week 4's int8 and latency work matter.
- **fp32 on Kaggle.** T5-family models are known to produce NaN loss in fp16, and T4/P100 have no
  bf16, so `--precision auto` picks fp32 there. If the run is too slow, try `--precision fp16` and
  watch the loss.
- **TextRank picked attachment placeholders.** SAMSum writes images and GIFs as `<file_gif>`;
  identical placeholder turns scored as highly similar and were selected. Placeholders are now ignored,
  and the row above was recomputed after the fix.
- **Merge note:** `summarize.py` conflicts with Mounika's stub at the same path (add/add). Take this
  version — it keeps her interface and her tests pass with it.

## Next (Week 2 — `week2-lahari-ami-chunking`)

- Run `train_samsum.ipynb` on Kaggle; commit the two rows, `run_info.json`, the notebook link and GPU time.
- Share `<hf-user>/flan-t5-base-samsum` with the team (read token) so Gate 1 can load it offline.
- `load_dialogsum`, `load_ami`, `ami_sections.py`, speaker-turn chunking, LoRA vs full, ablations.
