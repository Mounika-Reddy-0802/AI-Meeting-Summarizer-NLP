# ml/

Lahari - the academic core: data prep, training, evaluation. **Training runs on Kaggle only**; laptops
run data checks, the extractive/zero-shot evaluations and tests.

## Layout

| Path | What |
|------|------|
| `data/prepare.py` | `load_samsum()` → `id, dialogue, summary` with `Speaker: text` lines; `load_dialogsum()`, `load_ami()` stubs (W2) |
| `data/format.py` | turn parsing, speaker tags on/off, filler removal, `summarize:` / `summarize <section>:` prefix |
| `metrics.py` | ROUGE-1/2/L/Lsum (stemmed, plain mean) and BERTScore F1 |
| `train.py` | Seq2SeqTrainer fine-tuning; `--lora`, `--push_to_hub`, `--resume_from_checkpoint hub` |
| `extractive_baseline.py` | TextRank over dialogue turns |
| `evaluate.py` | `--system extractive\|zero-shot\|finetuned` → `benchmarks/raw/results.csv` + regenerated `benchmarks/summarization_results.md` |
| `kaggle/train_samsum.ipynb` | clone → install → train → test evaluation on Kaggle |
| `tests/` | `pytest ml/tests` |
| `checkpoints/` | gitignored; training output |

## Laptop setup

```powershell
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r ml/requirements.txt
pytest ml/tests
python ml/data/prepare.py --dataset samsum
python ml/evaluate.py --system extractive
python ml/evaluate.py --system zero-shot           # flan-t5-base on CPU, see the csv for wall time
```

On Windows keep the venv on a short path: torch has header files deep enough to hit the 260-character
path limit inside long folders.

## Kaggle run (exact steps)

1. **Accounts, once:** Kaggle account with phone verification (needed for GPUs and internet). Hugging
   Face account; create a **write** token at https://huggingface.co/settings/tokens.
2. **New notebook:** Kaggle → Code → New Notebook → File → *Import Notebook* → upload
   `ml/kaggle/train_samsum.ipynb` (or paste the cells).
3. **Settings panel:** Accelerator → **GPU T4 x2**; Internet → **on**; Persistence → *Files only*.
4. **Secret:** Add-ons → Secrets → add `HF_TOKEN` = the write token → tick it for this notebook.
5. **Branch:** in the second code cell set `BRANCH` (`week1-lahari-samsum-finetune` until week 1 is
   merged, `dev` afterwards).
6. **Run:** *Save Version* → *Save & Run All (Commit)*. This runs in the background (~2–3 h on T4) and
   keeps the logs even if the browser is closed. The model goes to a **private** Hub repo
   `<hf-user>/flan-t5-base-samsum`, one checkpoint per epoch.
7. **If the session dies:** set `RESUME = True` and *Save & Run All* again — `train.py` downloads
   `last-checkpoint/` from the Hub and continues.
8. **Collect results:** open the finished version → *Output* → download `outputs/`. Copy `results.csv`
   and the predictions `.jsonl` into `benchmarks/raw/`, `run_info.json` to
   `benchmarks/raw/train_flan-t5-base-samsum.json`, run `python ml/evaluate.py --table`, and put the
   notebook version URL and run time in the weekly doc.
9. **For the backend:** `huggingface-cli download <hf-user>/flan-t5-base-samsum --local-dir models/summarizer`
   (the repo is private, so log in with a read token first). `backend/app/services/summarize.py` loads it
   from `MODEL_DIR/summarizer`.

## Training defaults and why

- `google/flan-t5-base` (250M), inputs 1024 tokens, targets 128, 3 epochs, AdamW lr 5e-5 (LoRA 1e-3),
  batch 8 × 2 accumulation per GPU, linear schedule with 5 % warmup, seed 42.
- Precision `auto`: bf16 on Ampere or newer GPUs, otherwise fp32. T5-family models are known to
  overflow to NaN loss under fp16, and T4/P100 have no bf16, so Kaggle runs are fp32. `--precision fp16`
  exists if we want to test it.
- Each epoch scores ROUGE on the first 300 validation dialogues (beam 4); the best epoch by ROUGE-L is
  kept. Final numbers always come from `evaluate.py` on the full test split, never from training logs.
- Input is `summarize:` + newline + `Speaker: text` lines, the same format the backend builds from a
  diarised transcript.
