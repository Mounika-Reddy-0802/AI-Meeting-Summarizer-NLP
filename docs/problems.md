# problems.md

What went wrong, why, how it was fixed, and what it cost. Newest last.

---

**2026-09-14 — `Samsung/samsum` no longer exists on the Hub (Lahari).**
Symptom: the dataset id in PROJECT_PLAN.md and BLUEPRINT.md returns "not found".
Fix: `knkarthick/samsum`, which serves parquet files with the original splits. It has 14,731 training
dialogues where the paper reports 14,732; validation (818) and test (819) match. Recorded in
`data/README.md` and in the `SAMSUM_REPO` comment in `ml/data/prepare.py`.
Cost: small — found by the Day 1 check, which is what the check is for.

**2026-09-14 — AMI is gated and MRDA is script-only (Lahari).**
Symptom: `knkarthick/AMI` refuses anonymous access; `eusip/silicone` contains only a loading script.
Cause: the AMI repo requires accepting its terms. `datasets` 4 no longer runs loading scripts.
Fix: AMI — accept the terms on the Hub before Week 2 (logged in `data/README.md`). MRDA — the same CSVs
download directly from `raw.githubusercontent.com/eusip/SILICONE-benchmark/main/mrda/`; passed to Krishna
for Week 2. `ml/requirements.txt` also pins `datasets<4` in case a script dataset is needed.
Still open: AMI terms.

**2026-09-14 — torch would not install: Windows path length (Lahari).**
Symptom: `pip install` failed with `No such file or directory` on a deep header file under
`torch/include/ATen/...`.
Cause: the virtualenv sat inside a long folder path, and torch's deepest files crossed Windows' 260-character limit.
Fix: create the venv on a short path (`C:\Users\<you>\.mlvenv`), never inside the OneDrive project
folder. Noted in `ml/README.md`.
Cost: one failed install of several minutes.

**2026-09-14 — TextRank crashed without scipy (Lahari).**
Symptom: `ModuleNotFoundError: No module named 'scipy'` from `networkx.pagerank`.
Cause: networkx computes PageRank with scipy but does not install it.
Fix: `scipy>=1.13,<2` added to `ml/requirements.txt`. Caught by `pytest ml/tests`, not in production.
Cost: minutes.

**2026-09-14 — ROUGE was not reproducible run to run (Lahari).**
Symptom: `rouge_score`'s `BootstrapAggregator` reports the middle of a random resample, so the same
predictions can give slightly different numbers.
Fix: `ml/metrics.py` reports the plain mean F-measure over the corpus. Every number in the report has
to regenerate exactly (GIT_RULES §4).
Cost: small.

**2026-09-14 — TextRank chose attachment placeholders as the summary (Lahari).**
Symptom: the first test prediction was `Hannah: <file_gif>` twice.
Cause: SAMSum writes images and GIFs as `<file_gif>`, `<file_photo>`, …; identical placeholder turns
looked maximally similar to each other, so PageRank ranked them highest.
Fix: placeholders are stripped before words are counted, and turns with no words are picked last; a
test covers it. The extractive row was recomputed after the fix — the committed row
(ROUGE-L 0.2313) is the only one in `benchmarks/raw/results.csv`.
Cost: one extra evaluation run. Lesson: read a few predictions before trusting a score.

**2026-09-14 — zero-shot Flan-T5 is too slow on the laptop CPU (Lahari).**
Symptom: a timing check took roughly 20 s per dialogue with beam 4, whether batched or not — about
4–5 hours for the 819-dialogue test set.
Fix: the zero-shot row runs in the Kaggle notebook, on the same GPU and settings as the fine-tuned row.
Consequence to carry forward: the "runs on a laptop" claim needs Week 4's int8 and latency work.
Cost: about 30 minutes of timing runs.

**2026-09-14 — no Kaggle credentials, so no checkpoint yet (Lahari).**
Symptom: `train_samsum.ipynb` is ready but has not run; there is no fine-tuned or zero-shot row and
`MODEL_DIR/summarizer` is empty.
Impact: this is the main Gate 1 blocker — the backend falls back to the first three segments.
Fix: run the notebook from my Kaggle account (GPU on, internet on, `HF_TOKEN` secret), about 2–3 h.
Still open.

**2026-09-16 — `summarize.py` was added on two branches (Lahari).**
Symptom: merging my branch after Mounika's gives an add/add conflict in
`backend/app/services/summarize.py`.
Cause: Mounika's Week 1 stub and my v1 live at the same path, as the plan intends.
Fix: take my version — same `summarize(segments) -> SummaryResult` interface. Checked on a throwaway
merge of all three Week 1 branches: her 15 tests pass and ruff is clean with it.

**2026-09-14 — create-next-app added tool-configuration files (Krishna).**
Symptom: the scaffold for `frontend/` came with two tool-configuration markdown files next to `package.json`.
Cause: current `create-next-app` templates ship those files by default.
Fix: deleted before the first `git add`; they were never committed. GIT_RULES §0 forbids tool
configuration anywhere in the tree, so read a generator's file list before staging it.
Cost: minutes, because it was caught before the commit rather than after.

**2026-09-14 — `.env.example` silently ignored (Krishna).**
Symptom: `frontend/.env.example` did not show up in `git status`.
Cause: the generated `frontend/.gitignore` ignores `.env*`, and a nested `.gitignore` overrides the
root file's `!.env.example`.
Fix: `frontend/.gitignore` now re-includes `!.env.example` directly under the `.env*` line.
Cost: small; it would have cost more if the missing template had been found by a teammate on a fresh clone.

**2026-09-14 — the mock showed a faithfulness score while a meeting was still processing (Krishna).**
Symptom: a freshly uploaded mock meeting displayed "faithfulness 0.75" during diarisation.
Cause: the mock copied the finished template meeting whole, including `faithfulness`.
Fix: the mock now blanks `faithfulness`, `participants`, minutes and action items until the stage that
fills them. Found by looking at the screenshots, not by the type checker.
Cost: small.

**2026-09-16 — PR #1 showed nine conflicting files against `main` (Krishna).**
Symptom: "This branch has conflicts that must be resolved" — `.env.example`, `.gitignore`,
`PROJECT_PLAN.md`, `README.md`, `data/README.md`, `docker-compose.yml`, `frontend/README.md`,
`frontend/src/components/README.md`, `ml/baselines/README.md` — and "14 commits" for a 5-commit branch.
Cause: two mistakes stacked. The PR targeted `main`, but weekly PRs go to `dev` (GIT_RULES §6). And
GitHub's `main` still holds the history from before the Day-0 cleanup (Mounika's Day-0 rewrite entry — its
force-push was rejected because `main` is protected), so it shares only its first commits with `dev`.
Fix: retarget the PR base to `dev`. Checked locally: the branch merges into `dev` with no conflicts,
on its own and after the other two Week 1 branches.
Still open: the retarget itself (a GitHub edit), and pushing the cleaned `main`.
Cost: the PR has been blocked since it was opened.

**2026-09-22 — the three sample meetings are not recorded (Krishna).**
Symptom: `demo/sample_audio/` holds only its README.
Cause: the Day-0.5 recording task needs the three of us together and was not scheduled.
Impact: blocks Mounika's `asr_latency.csv` and the Gate 1 demo with real audio.
Fix: record three 3–5 minute meetings with 2–3 speakers (≤ 10 MB each) and note consent in
`docs/decisions.md`.
Still open.
