# problems.md

What went wrong, why, how it was fixed, and what it cost. Newest last.

---

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
