# CLAUDE.md — AI Meeting Summarizer (NLP)

## What this project is
Academic NLP project by Krishna, Lahari and Mounika. Deepgram does speech-to-text; OUR OWN
fine-tuned Hugging Face seq2seq model (Flan-T5) does summarization; action-item extraction and
semantic search are our own code. No LLM API (Gemini, GPT, Claude, etc.) is ever called in the
application path — only as an offline baseline in ml/baselines/. Everything is built from scratch
in this repo; never look for, copy or reference any earlier project.

## Source of truth
- PROJECT_PLAN.md — what to build, who owns what, week by week, in what order.
- GIT_RULES.md — branches, commits, PRs, docs. Mandatory.
Read both at the start of every session before doing anything. If a request conflicts with them,
say so and ask, don't silently deviate.

## Identity
The current member is set in .claude/member (one word: krishna | lahari | mounika). Read it first.
Only touch that member's owned folders (PROJECT_PLAN.md §1). If a task needs a file outside them,
stop and say which file and why; the owner must approve.

## Git rules you must enforce on yourself
- Never commit to main or dev. Work only on week<N>-<name>-<topic> branches created from latest dev.
- Before the first commit of a session: `git branch --show-current` and confirm it matches the
  member and week. If not, stop.
- Commit messages: short lowercase imperative, one logical change, number in the message when a
  number changed. No prefixes, no "update", no "fix", no "wip" as the final commit.
- One commit per numbered task in PROJECT_PLAN.md unless the task is clearly two changes.
- Push after every commit (`git push -u origin <branch>`).
- Never delete a branch. Never rebase or squash. Never force-push.
- Never commit: .env files, API keys, tokens, *.db, audio files (except demo/sample_audio/),
  ml/checkpoints/, notebook outputs. Check `git status` and `git diff --cached --stat` before
  every commit and refuse if any of these appear.

## Secrets and accounts
- .env.example files contain names only. Real keys live in .env, which is gitignored.
- If a key is missing, print exactly which variable and where to get it, then wait.
  You cannot create GitHub, Kaggle, Hugging Face or Deepgram accounts — the human does that.

## Training policy
All model training runs on Kaggle GPUs, never on this machine. You write ml/train.py and
ml/kaggle/*.ipynb; the human runs the notebook on Kaggle and reports the notebook URL and numbers.
Never start a training run locally. Local inference on a downloaded checkpoint is fine.

## Numbers
Every number that will appear in a doc or report must be produced by a script that writes to
benchmarks/raw/. Never type a number into a markdown table by hand; generate the table.

## Session protocol
1. Read CLAUDE.md, PROJECT_PLAN.md, GIT_RULES.md, .claude/member, current branch.
2. State: member, week, branch, and the next unfinished task number from PROJECT_PLAN.md.
3. Do ONE task. Show the diff summary. Commit and push with a compliant message.
4. Print: files changed, how to run, what to test manually. Stop and wait.
5. At the end of the week's tasks: write docs/W<N>_<name>_<topic>.md (what I built, how to run,
   numbers, what's next), update benchmarks/ if numbers were produced, then open the PR to dev with
   `gh pr create` using .github/pull_request_template.md and the title format
   [W<N>] <Name>: <topic summary>. Never merge a PR yourself.

## Code standards
- Python 3.11, type hints, ruff clean, pytest for backend.
- TypeScript strict, `npm run build` must pass.
- Small functions, docstrings on public functions, no dead code, no TODO left in a PR except the
  stubs PROJECT_PLAN.md explicitly asks for.
