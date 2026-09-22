# problems.md

What went wrong, why, how it was fixed, and what it cost. Newest last.

---

**2026-09-14 — Day-0 history rewrite (Mounika).**
Symptom: a tool configuration file and its commit were on `main`, and two earlier Day-0 commits still
mentioned tool names (a prompts section in the old plan, two `.gitignore` lines).
Fix: rewrote the Day-0 commits to drop that file, those lines and that section, keeping every other
commit with its original author, date and message; then one commit moving to the four-week plan.
`dev` and the re-pointed `repo-init` tag were force-pushed with `--force-with-lease`.
Still open: `main` is protected on GitHub, so its force-push was rejected; it needs protection relaxed
for one push and then restored. Krishna and Lahari must clone fresh after that.
Cost: about 1.5 h, mostly OneDrive locking files inside `.git` during the rewrite (pause OneDrive
syncing before any bulk git operation).

**2026-09-14 — Empty values in backend/.env broke settings (Mounika).**
Symptom: after `Copy-Item .env.example .env`, empty `DATABASE_URL=` / `MODEL_DIR=` replaced the defaults.
Fix: settings ignore empty variables and require a `JWT_SECRET` of at least 32 characters.
Cost: 15 min.

**2026-09-14 — the Day-0 rewrite left `main` behind, and PRs against it show false conflicts (Mounika).**
Update to the first entry. Because `main`'s force-push was rejected, GitHub's `main` still has the old
Day-0 commits, including the tool-configuration file, while `dev` has the rewritten ones. They share
only the first commits, so any PR opened against `main` lists every Day-0 file as a conflict — this is
what blocked Krishna's PR #1 on 16 Sep. Weekly PRs go to `dev`, where all three Week 1 branches merge
cleanly. My local `main` is already the cleaned history (identical to `dev`).
Fix: relax the protection on `main` for one `git push --force-with-lease origin main`, restore it, and
have Krishna and Lahari re-clone. Needs all three to agree (GIT_RULES §11).
Still open.

**2026-09-22 — pyannote not downloaded, so diarisation and the ASR timing are blocked (Mounika).**
Symptom: `MODEL_DIR` has faster-whisper `small`, MiniLM and the NLI cross-encoder, but no pyannote;
`benchmarks/raw/asr_latency.csv` does not exist.
Cause: `backend/.env` has no `HF_TOKEN`, and the `speaker-diarization-3.1` / `segmentation-3.0` terms
have to be accepted on the Hub first. The timing script also needs Krishna's three sample clips.
Fix: accept both terms, put a read token in `backend/.env`, run `python scripts/download_models.py`,
then `python scripts/asr_latency.py` once the clips exist.
Still open — it is part of Gate 1.
