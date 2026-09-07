# GIT_RULES.md

Repository workflow rules for the 3-member team: **Krishna · Lahari · Mounika**

Week-branch pattern (`week<N>-<name>-<work-topic>`) with per-member contribution tracking. These
rules are **mandatory**. They exist so that (a) faculty can see each member's weekly contribution at
a glance, and (b) the repo itself is a portfolio artifact.

**Project scope:** Deepgram for speech-to-text; our own fine-tuned model for summarization; our own
action-item extraction and semantic search; FastAPI + SQLite backend; Next.js frontend. No LLM APIs
(Gemini etc.) in the application path — they exist only as offline baselines.

---

## 1. Repository structure

```
AI-Meeting-Summarizer/
├── README.md                  # overview, architecture image, quickstart, results table
├── GIT_RULES.md               # this file
├── PROJECT_PLAN.md            # the 3-week from-scratch plan
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
│   ├── app/routes/            # auth.py, meetings.py
│   ├── app/services/
│   │   ├── transcribe.py      # Mounika — Deepgram prerecorded, diarize=true
│   │   ├── summarize.py       # Lahari  — loads checkpoint, hierarchical chunking
│   │   ├── action_items.py    # Krishna — spaCy rules / classifier
│   │   └── search.py          # Mounika — Sentence-BERT semantic search
│   ├── scripts/seed.py
│   ├── requirements.txt
│   └── .env.example           # DEEPGRAM_API_KEY, JWT_SECRET, MODEL_PATH — names only
├── ml/                        # Lahari — the academic core
│   ├── data/prepare.py        # SAMSum / DialogSum / AMI loaders
│   ├── train.py
│   ├── evaluate.py
│   ├── extractive_baseline.py
│   ├── baselines/gemini_baseline.py   # offline only
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
├── W2_krishna_action_items.md
├── W2_lahari_ami_and_chunking.md
├── W2_mounika_semantic_search.md
├── W3_krishna_demo_and_export.md
├── W3_lahari_evaluation_report.md
├── W3_mounika_docker_release.md
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
├── summarization_results.md   # ROUGE-1/2/L, BERTScore: extractive · zero-shot · fine-tuned · Gemini
├── ablations.md               # speaker tags on/off, filler removal on/off, chunk size
├── action_item_eval.md        # precision/recall/F1 on the labeled set
├── human_eval.md              # coherence / coverage / factuality, 1-5, 3 raters
├── latency.md                 # inference time CPU vs GPU vs Gemini API
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
| 1 | `week1-krishna-frontend` | `week1-lahari-samsum-finetune` | `week1-mounika-fastapi-backend` |
| 2 | `week2-krishna-action-items` | `week2-lahari-ami-chunking` | `week2-mounika-semantic-search` |
| 3 | `week3-krishna-demo-export` | `week3-lahari-evaluation-report` | `week3-mounika-docker-release` |

Rules:

- The topic is the **work**, not the role: `week2-mounika-semantic-search`, never
  `week2-mounika-backend-stuff`.
- Lowercase, hyphen-separated, no underscores or spaces.
- Branch from the latest `dev` on Day 1 of the week. Never branch from another member's weekly
  branch.
- Branches are **never deleted** after merge — the branch list is the progress record.
- No shared branches. Pairing happens on the owner's branch; the helper reviews the PR.

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
   W3 Lahari) opens `dev` to `main` titled `Week N: <gate summary>`, merges, and tags:

```bash
git tag -a week1-complete -m "Gate 1: no AWS, audio -> Deepgram -> own model -> summary in UI"
git tag -a week2-complete -m "Gate 2: AMI checkpoint, chunking, action items, semantic search"
git tag -a week3-complete -m "Gate 3: results table, docker demo, report"
git tag -a v2.0           -m "Final release"
git push --tags
```

### Week gates

- **Gate 1:** `docker compose up` (or two terminals) starts the app with zero AWS; one real audio
  file goes upload -> Deepgram -> fine-tuned SAMSum checkpoint -> summary on screen.
- **Gate 2:** a 20-minute recording produces a coherent summary via hierarchical chunking, action
  items with owners linked to transcript lines, and a working semantic search;
  `benchmarks/summarization_results.md` has at least 4 rows.
- **Gate 3:** full results + ablations + human eval in `benchmarks/`, seed data, export, demo video,
  README with architecture and results table.

A member who finishes early reviews PRs or drafts their report section. They do **not** start next
week's branch until `dev` to `main` for the current week is merged.

---

## 7. Commit quality rules

**Format:** short lowercase imperative naming the change. No bracketed prefix, no area tag, no body
unless genuinely needed. If it sounds like something you'd say to a teammate, it's right.

### Good commits

```
add fastapi skeleton with sqlite models and jwt auth
parse deepgram utterances into transcript segments with diarization
replace cognito login with email password jwt
fine-tune flan-t5-base on samsum, rouge-l 0.41 on test
chunk transcripts on speaker turns at 800 tokens with 100 overlap
speaker tags in input raise rouge-l 0.38 -> 0.42 on ami
extract action items by imperative root verb and modal patterns
label 300 ami sentences for action item classifier
embed segments with minilm and add cosine search endpoint
export summary and transcript as docx
```

### Banned commits (instant PR rejection)

```
update            final           final2            asdf
changes           work done       minor fix         commit
updated code      week2 work      krishna changes   pushed files
[W2][ML] ...      any bracketed prefix at all
```

Rules:

- A commit is a unit of work you'd describe out loud, not a save point. Prefer four commits with
  weight over fifteen that each touch one file.
- One logical change per commit. "Built the whole backend" is a branch, not a commit — break it
  into: skeleton, models, auth, upload route, pipeline task.
- The message must let a teammate know what changed without opening the diff. If a commit changed a
  number, put the number in the message — these become contribution highlights.
- Commit working code. Broken WIP at end of session: `wip: chunk merge losing last segment, see
  TODO` — and it may **not** be the branch's final commit before the PR.
- **Never commit:** audio datasets, `.env`, API keys, `*.db`, model checkpoints, notebook output
  cells (`nbstripout --install`). Sample audio in `demo/sample_audio/` is the only allowed audio.
- If a secret is ever committed: rotate the key immediately, add an entry in `problems.md`, and do
  **not** try to hide it with a force-push.

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

1. **Branch list** — 9 branches, `week<N>-<name>-<topic>`, a per-member timeline.
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
- All training runs on Kaggle, never on personal laptops. The Kaggle notebook link and run time go
  in the weekly doc; a training number without a Kaggle run behind it is not accepted.

---

Adopt this file as-is in the repo root. Any rule change requires agreement of all three members and
a commit to this file explaining the change.
