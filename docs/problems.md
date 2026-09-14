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
