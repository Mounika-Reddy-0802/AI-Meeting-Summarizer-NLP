# GIT_RULES.md

Repository workflow rules for the 3-member team: **Krishna · Lahari · Mounika**

Four-week branch pattern (`week<N>-<name>-<work-topic>`) with per-member contribution tracking. These
rules are **mandatory**. They exist so that (a) faculty can see each member's weekly contribution at
a glance, and (b) the repo itself is a portfolio artifact.

**Project scope:** local speech-to-text and diarisation (faster-whisper + pyannote); our own fine-tuned
model for structured minutes; our own dialogue-act tagger, action-item extraction, evidence linking and
hybrid search; FastAPI + SQLite backend; Next.js frontend. No cloud service and no LLM API in the
application path — an LLM exists only as an offline baseline script in `ml/baselines/`.

---

## 0. Only the three members appear — strict, permanent, whole repository

Editors, code generators, scripts, bots and any other tool are never contributors. On **every branch,
every commit, every PR**:

- Never add a `Co-authored-by:` trailer for anyone who is not Krishna, Lahari or Mounika.
- Never use a tool's, bot's or third party's name, username or email as git author, committer or identity.
- Never configure anything other than your own GitHub identity as `user.name` / `user.email`, locally or globally.
- No tool name, tool-generated footer ("Generated with …", "Made by …") or tool configuration file appears in
  commit metadata, commit messages, PR titles, PR descriptions, or anywhere in the tree.
- Nobody but the three members ever shows up under GitHub Insights -> Contributors.

Every commit is authored **and** committed by the member who owns the branch (§5, §9) — nobody else. Before
every commit, verify author, committer and trailers (§7 "Before every commit").

This rule overrides any default behaviour of any tool being used.

---

## 1. Repository structure

```
AI-Meeting-Summarizer/
├── README.md                  # overview, architecture image, quickstart, results table
├── GIT_RULES.md               # this file
├── PROJECT_PLAN.md            # the 4-week from-scratch plan
├── BLUEPRINT.md               # architecture, NLP design, evaluation design, viva prep
├── .gitignore                 # data/, .env*, ml/checkpoints/, __pycache__, node_modules, *.db, *.wav, *.mp3
├── docker-compose.yml
├── frontend/                  # Krishna — Next.js app
│   ├── src/components/
│   ├── src/lib/               # api.ts, auth.tsx
│   ├── src/pages/
│   └── .env.example           # NEXT_PUBLIC_API_URL only
├── backend/                   # Mounika — FastAPI
│   ├── app/main.py
│   ├── app/db.py, models.py, schemas.py, auth.py
│   ├── app/routes/            # auth.py, meetings.py, search.py
│   ├── app/services/
│   │   ├── transcribe.py      # Mounika — faster-whisper, local
│   │   ├── diarize.py         # Mounika — pyannote, local
│   │   ├── summarize.py       # Lahari  — loads checkpoint, chunking, section-conditioned minutes
│   │   ├── dialogue_acts.py   # Krishna — MRDA-trained tagger
│   │   ├── action_items.py    # Krishna — rules / classifier / owner resolution
│   │   ├── evidence.py        # Mounika — hybrid retrieval + NLI entailment, faithfulness score
│   │   └── search.py          # Mounika — BM25 + dense hybrid search
│   ├── scripts/seed.py
│   ├── requirements.txt
│   └── .env.example           # JWT_SECRET, MODEL_DIR, WHISPER_SIZE — names only
├── ml/                        # Lahari — the academic core
│   ├── data/prepare.py        # SAMSum / DialogSum / AMI loaders; ami_sections.py; qmsum.py
│   ├── train.py
│   ├── evaluate.py
│   ├── extractive_baseline.py
│   ├── baselines/llm_baseline.py      # offline only, never imported by backend/
│   ├── dialogue_acts/         # Krishna — MRDA preparation + tagger training
│   ├── action_items/          # Krishna — labeled sentences + classifier training
│   ├── kaggle/                # training notebooks run on Kaggle GPUs (outputs stripped)
│   ├── checkpoints/           # gitignored; downloaded from HF Hub for inference only
│   └── notebooks/             # exploration only: w2_lahari_ami_eda.ipynb naming
├── docs/                      # week-wise documentation (§2)
├── demo/                      # demo assets (§3)
├── benchmarks/                # evaluation results (§4)
└── data/                      # gitignored; data/README.md explains how to download
```

Folder owner reviews any PR that touches their folder. Cross-folder changes need the owner's
approval.

---

## 2. `docs/` — week-wise documentation

Exactly one markdown file per member per week — `W<N>_<name>_<main task>.md`:

```
docs/
├── W1_krishna_frontend.md
├── W1_lahari_samsum_finetune.md
├── W1_mounika_fastapi_backend.md
├── W2_krishna_dialogue_acts.md
├── W2_lahari_ami_chunking.md
├── W2_mounika_hybrid_search.md
├── W3_krishna_action_items.md
├── W3_lahari_structured_minutes.md
├── W3_mounika_evidence_linking.md
├── W4_krishna_demo_export.md
├── W4_lahari_evaluation_report.md
├── W4_mounika_docker_release.md
├── decisions.md               # running log from weekly syncs
├── problems.md                # what went wrong, why, how it was fixed
└── results.md                 # frozen numbers (Lahari owns)
```

Each weekly doc is short (half a page is fine) and answers: what I built, how to run it, what the
numbers/outputs are, what's next. Written **before** opening the weekly PR — the PR is not
reviewable without it.

A week's work goes in one file even if several tasks produced it. Same rule for branches (§5): one
per member per week, side fixes included.

`problems.md` is everyone's. Add an entry the day you lose time to something — symptom, cause, fix,
what it cost.

---

## 3. `demo/`

```
demo/
├── demo_script.md             # rehearsed viva flow, step by step
├── screenshots/               # W1_upload.png, W2_action_items.png …
├── sample_audio/              # 3 short meeting recordings (<= 5 min, <= 10 MB each) used by seed.py
├── sample_outputs/            # the summaries/action items those recordings produce
└── video/                     # final 2-3 min screen recording (or link in README)
```

---

## 4. `benchmarks/`

```
benchmarks/
├── summarization_results.md   # ROUGE-1/2/L, BERTScore: extractive · zero-shot · fine-tuned · LoRA · LLM baseline
├── structured_minutes.md      # per-section: generic-split vs section-conditioned vs DA-filtered
├── ablations.md               # speaker tags on/off, filler removal on/off, chunk size, LoRA vs full
├── dialogue_act_eval.md       # macro-F1, confusion matrix on MRDA
├── action_item_eval.md        # precision/recall/F1 and owner accuracy on the labeled set
├── factuality.md              # NLI faithfulness per system; flag precision/recall
├── search_eval.md             # substring vs BM25 vs dense vs hybrid, hits@5 / MRR
├── human_eval.md              # coherence / coverage / factuality, 1-5, 3 raters
├── latency.md                 # per-stage CPU time, fp32 vs int8
└── raw/                       # results.csv and json produced by ml/evaluate.py
```

Every number in the report must be traceable to a file in `benchmarks/raw/` produced by a script in
`ml/` or `backend/`. **Numbers typed by hand into a table are not accepted.**

---

## 5. Branch model

### Permanent branches

- `main` — only stable, demo-ready, reviewed code. **Nobody commits directly to `main`. Ever.**
- `dev` — integration branch where the week's PRs land first.
- `repo-init` — tag on the empty-skeleton commit (Day 0). The project timeline starts here.

### Weekly work branches

One per member per week, `week<N>-<name>-<work-topic>`:

| Week | Krishna | Lahari | Mounika |
|------|---------|--------|---------|
| 1 | `week1-krishna-frontend` | `week1-lahari-samsum-finetune` | `week1-mounika-local-asr-backend` |
| 2 | `week2-krishna-dialogue-acts` | `week2-lahari-ami-chunking` | `week2-mounika-hybrid-search` |
| 3 | `week3-krishna-action-items` | `week3-lahari-structured-minutes` | `week3-mounika-evidence-linking` |
| 4 | `week4-krishna-demo-export` | `week4-lahari-evaluation-report` | `week4-mounika-docker-release` |

Rules:

- The topic is the **work**, not the role: `week2-mounika-semantic-search`, never
  `week2-mounika-backend-stuff`.
- Lowercase, hyphen-separated, no underscores or spaces.
- Branch from the latest `dev` on Day 1 of the week. Never branch from another member's weekly
  branch.
- Branches are **never deleted** after merge — the branch list is the progress record.
- No shared branches. Pairing happens on the owner's branch; the helper reviews the PR.
- No other branches. Apart from `main`, `dev`, the twelve weekly branches and a demo-day `hotfix-<topic>`
  (§10), do not create branches.
- Never merge a branch or rewrite its history outside the cycle in §6 and §11.

---

## 6. Weekly merge cycle (completion-based)

A "week" ends when its tasks are done and the gate passes — 5 days or 8, whichever it takes.

1. **Start of week:** create your `week<N>-<name>-<topic>` branch from the latest `dev`.
2. **During the week:** commit to your own branch every day you work (§7). Push the same day —
   unpushed work doesn't exist.
3. **When your week's work is complete:** write `docs/W<N>_<name>_<topic>.md`, update `benchmarks/`
   if you produced numbers, open a PR to `dev`, message the group: "Week N done — PR up."
4. **Review:** Krishna and Lahari review each other; Mounika is reviewed by whoever is free.
   Reviewer checklist in §8. Merge with a merge commit (no squash, no rebase on shared branches).
5. When all three PRs are merged and the gate passes, one member (rotating: W1 Mounika, W2 Krishna,
   W3 Lahari, W4 Mounika) opens `dev` to `main` titled `Week N: <gate summary>`, merges, and tags:

```bash
git tag -a week1-complete -m "Gate 1: offline audio -> local asr -> own model -> summary in UI"
git tag -a week2-complete -m "Gate 2: AMI checkpoint, chunking, dialogue acts, hybrid search"
git tag -a week3-complete -m "Gate 3: structured minutes, evidence linking, action items, export"
git tag -a week4-complete -m "Gate 4: results tables, human eval, docker demo, report"
git tag -a v1.0           -m "Final release"
git push --tags
```

### Week gates

- **Gate 1:** the app starts with no cloud service; one real audio file goes upload -> local ASR +
  diarisation -> fine-tuned SAMSum checkpoint -> summary on screen, with the network disabled.
- **Gate 2:** a 20-minute recording produces a coherent summary via hierarchical chunking, a
  dialogue-act-tagged transcript, rule-based action items linked to transcript lines, and working
  hybrid search; `benchmarks/summarization_results.md` has at least 5 rows.
- **Gate 3:** Decisions / Actions / Problems minutes with per-sentence evidence and faithfulness flags,
  action items with owners, docx export; `structured_minutes.md`, `factuality.md`, `action_item_eval.md` exist.
- **Gate 4:** all benchmark tables + human eval in `benchmarks/`, seed data, demo video, README with
  architecture and results table, `docker compose up` on a clean machine.

A member who finishes early reviews PRs or drafts their report section. They do **not** start next
week's branch until `dev` to `main` for the current week is merged.

---

## 7. Commit quality rules

**Format:** short lowercase imperative naming the change. No bracketed prefix, no area tag, no body
unless genuinely needed. If it sounds like something you'd say to a teammate, it's right. Aim for
about 50 characters; go longer only when a number or a specific detail needs the room.

**Core principle:** fewer, stronger commits beat many small ones. Before committing, ask: *"Is this
worth appearing in the project's history?"* If not, keep working and group it with related work.

A commit-worthy unit is one of: a completed feature, a substantial bug fix, a meaningful refactor, a
completed module or pipeline stage, a meaningful documentation update, a plan/roadmap milestone, or a
coherent group of related changes. Not commit-worthy: one small line, one reworded sentence, formatting,
a tiny doc correction, an import cleanup, one insignificant file, or repeated "fix"/"update"/"change"
commits for the same piece of work.

### Good commits

```
add fastapi skeleton with sqlite models and jwt auth
cache transcripts by file hash so audio is never transcribed twice
align whisper words to pyannote turns into speaker segments
fine-tune flan-t5-base on samsum, rouge-l 0.41 on test
chunk transcripts on speaker turns at 800 tokens with 100 overlap
speaker tags in input raise rouge-l 0.38 -> 0.42 on ami
tag segments with mrda dialogue acts, macro-f1 0.71
extract action items by imperative root verb and modal patterns
label 300 ami sentences for action item classifier
fuse bm25 and minilm scores with rrf, hits@5 0.80 -> 0.88
link minute sentences to segments by nli entailment
export summary and transcript as docx
```

### Banned commits (instant PR rejection)

```
update            final           final2            asdf
changes           work done       minor fix         commit
updated code      week2 work      krishna changes   pushed files
[W2][ML] ...      any bracketed prefix at all
```

A bare `update` or `fix` is banned; a specific one is fine: `fix speaker merge dropping last turn`,
`update whisper size from base to small`.

### Also banned — inflated messages

```
implement comprehensive architecture      introduce advanced functionality
enhance robust pipeline                   complete implementation of ...
add extensive improvements                improve overall system
refactor architecture                     optimize pipeline architecture
```

Say what changed, not how impressive it is.

Rules:

- A commit is a unit of work you'd describe out loud, not a save point. Prefer four commits with
  weight over fifteen that each touch one file.
- One logical change per commit. "Built the whole backend" is a branch, not a commit — break it
  into: skeleton, models, auth, upload route, pipeline task.
- Don't split artificially. A single feature's code, config, helpers and docs go in **one** commit —
  never spread across several to inflate the commit count. Don't mix unrelated work either.
- No commits for trivia: a one-line tweak, a reworded sentence, formatting, an import cleanup. Fold
  them into the next meaningful commit on the same work.
- Don't leave finished work uncommitted: finish, verify it works, review the diff, commit, push, then
  move on.
  In full, when a meaningful piece of work is complete: (1) finish the implementation, (2) verify the
  project still works, (3) review the changed files, (4) check only intended changes are included,
  (5) create one focused commit, (6) push it, (7) then start the next task.
- Commit messages are written by the member, in their own words, describing what actually changed —
  never exaggerated, never generated boilerplate.
- The message must let a teammate know what changed without opening the diff. If a commit changed a
  number, put the number in the message — these become contribution highlights.
- Commit working code. Broken WIP at end of session: `wip: chunk merge losing last segment, see
  TODO` — and it may **not** be the branch's final commit before the PR.
- **Never commit:** audio datasets, `.env`, API keys, `*.db`, model checkpoints, notebook output
  cells (`nbstripout --install`). Sample audio in `demo/sample_audio/` is the only allowed audio.
- If a secret is ever committed: rotate the key immediately, add an entry in `problems.md`, and do
  **not** try to hide it with a force-push.

### Before every commit

Never blindly `git add -A`. Check each item:

1. `git status` — only intended files; nothing unrelated.
2. `git diff --cached` — read the actual diff, not just the file list.
3. No secrets, `.env`, `.git.env`, `*.db`, audio, checkpoints or notebook outputs (list above).
4. The project still runs / tests pass where practical.
5. `git config user.name` and `git config user.email` are the **branch owner's** (§9). One laptop
   may be shared, so check every session.
6. Only a member identity in author, committer, message or trailers (§0). After committing:
   `git log -1 --format='%an <%ae> | %cn <%ce>%n%B'`.

### Pushing

- Push to the existing remote `origin` only. Never create another repository and never change the
  remote without the whole team agreeing.
- Assume the existing remote and the member's configured credentials are correct; never switch to
  another account.
- Push with the branch owner's own GitHub account.
- Push to the branch you committed on, right after the commit.
- Never force-push (see §11 for the one exception).

---

## 8. Pull request rules

**PR title:** `[W<N>] <name>: <work-topic summary>`
e.g. `[W2] Lahari: AMI fine-tune + hierarchical chunking (rouge-l 0.42)`

**PR description** (`.github/pull_request_template.md`):

- What changed (3-6 lines)
- Verify step: exact commands the reviewer runs
- Numbers produced (if any) and the `benchmarks/raw/` file they came from
- Link to the weekly doc

**Reviewer must** (15 minutes, not a formality):

- Pull the branch and run the verify step.
- Scan commit messages for §7 compliance.
- Confirm the weekly doc exists and matches the code.
- Leave at least one substantive comment (question, suggestion, or "verified X works").

---

## 9. Contribution visibility

The workflow produces four proofs of individual weekly contribution:

1. **Branch list** — 12 branches, `week<N>-<name>-<topic>`, a per-member timeline.
2. **Commit history** — daily, self-describing commits under each member's own identity. Configure
   before Week 1 with the email on your GitHub account:

```bash
git config user.name  "Lahari"
git config user.email "<github-account-email>"
```

3. **`docs/`** — one signed weekly write-up per member.
4. **PRs + reviews** — who built what, who verified what.

GitHub Insights -> Contributors reflects true effort only if §7 is followed.

---

## 10. Conflict and emergency rules

- Merge conflicts are resolved by the branch owner, with the folder owner (§1) consulted.
- Hotfix on `main` (demo-day only): `hotfix-<topic>` from `main`, PR back to **both** `main` and
  `dev`, reviewed by any teammate. Not a backdoor around the weekly cycle.
- If a member's week slips: the PR still opens when the team closes the week, with whatever is done
  plus the doc stating what's missing; the gap moves to next week's branch. An honest partial PR
  beats a silent missing week.
- Model checkpoints are shared via Hugging Face Hub (private repo), never via git.
- All training runs on Kaggle, never on personal laptops. Kaggle and the Hub are training and storage
  infrastructure only; the running application never calls any external service. The Kaggle notebook link and run time go
  in the weekly doc; a training number without a Kaggle run behind it is not accepted.

---

## 11. History rewrites

Default: **never**. A rewrite happens only to fix commit metadata (wrong author, committer, or a
non-member identity/trailer), or the one Day-0.5 cleanup logged in `problems.md`, and pushing it needs explicit approval from the branch owner — plus the whole team if
the branch is `main` or `dev`.

When a rewrite is approved:

- Change metadata only. File contents and code stay exactly as they were.
- Keep the same commits in the same order, with the same messages.
- Keep the original author **and** committer dates. Rewritten commits must not look like they were
  made today.
- Remove the unwanted author, committer or co-author data. Never add a non-member identity while doing it.
- Verify before pushing: `git log --format='%h %an <%ae> %ad | %cn <%ce> %cd'`, and
  `git diff <old-tip> <new-tip>` must be empty.
- Force-push only after that approval, with `--force-with-lease`, and log it in `problems.md`.

The objective of any approved rewrite: **same project content + same commit timeline + corrected
metadata.** Nothing else changes.

A leaked secret is **not** a reason to rewrite. Rotate the key instead (§7).

---

## 12. Permanent priorities — apply to everything, every branch, every task

These rules apply to the entire repository and all future work unless all three members change them.

1. **Only the three members appear anywhere in git metadata** (§0).
2. **Meaningful commits only** (§7).
3. **Group related work instead of creating tiny commits** (§7).
4. **Keep the history clean, natural and professional** (§7, §8).
5. **Verify changes before committing** (§7 "Before every commit").
6. **Use only your own git identity** (§9).
7. **Push meaningful completed work to the existing repository only** (§7 "Pushing").

### Most important rule

> **Never let anyone or anything other than Krishna, Lahari or Mounika appear as contributor, author,
> co-author, committer or trailer — and never create meaningless commits just to increase the count.**

---

Adopt this file as-is in the repo root. Any rule change requires agreement of all three members and
a commit to this file explaining the change.
