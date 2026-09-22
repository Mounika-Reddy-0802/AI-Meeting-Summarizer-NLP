# W1 · Krishna — frontend

Branch `week1-krishna-frontend` · PROJECT_PLAN.md §5 Krishna tasks 1–7 · Gate 1 (UI half)

## What I built

**Next.js app** — `frontend/`. Next.js 16 (pages router), TypeScript `strict`, Tailwind 4, ESLint.
`frontend/.env.example` holds one variable, `NEXT_PUBLIC_API_URL`; nothing else is configurable, so
there is nothing secret to leak from the client.

**Typed contract** — `src/lib/types.ts`. Every request and response in PROJECT_PLAN.md §3, including
`minutes` with `evidence`, `entailment` and `supported`, the `faithfulness` block and all eight status
values. The fields the pipeline fills late (`entailment`, `supported`, `faithfulness.score`,
`dialogue_act`) are typed `| null`, because the backend sends `null` until that stage has run —
typing them as plain numbers would have compiled and then crashed on the first real meeting.

**API client** — `src/lib/api.ts`. One function per endpoint (register, login, upload, list, get,
status, evidence, delete, export, search). It adds `Authorization: Bearer`, turns FastAPI's `detail`
(a string, or a list of validation errors) into one readable message, and says *"Cannot reach the API
at …"* instead of a bare `TypeError` when the backend is down.

**Auth** — `src/lib/auth.tsx`. Token in `localStorage`; `useRequireAuth` sends signed-out visitors to
`/login?next=…`; any 401 logs out everywhere through one handler rather than per page.

**Mock API** — `mock/db.json` + `mock/server.cjs` (json-server 0.17, port 4000). The same routes as the
backend with three meetings — finished with minutes and evidence, still summarizing, and failed with
the backend's real error text. An upload walks the five stages, 3 s each, so the polling UI was built
and tested before the backend existed. Nothing is ever written back to `db.json`.

**Pages**

| Page | What it does |
|---|---|
| `login`, `register` | one shared form; the 8-character password rule matches the backend |
| `dashboard` | meetings newest first, status badge, summary snippet; refreshes every 5 s while anything is processing; delete for finished meetings |
| `summariser` | title + upload (drag and drop, the backend's own extension list and 500 MB limit) or record in the browser |
| `meetings/[id]` | polls `/status` every 2 s with a stage stepper and elapsed time, reloads the meeting when the stage changes; failed meetings show the backend's reason; summary + faithfulness, Decisions / Actions / Problems tabs with an *unsupported* badge, action items with owner / due / confidence, speaker-grouped transcript |

**Components** — `Layout`, `AuthForm`, `Recorder` (MediaRecorder → webm/ogg/m4a with a preview player),
`UploadAudio`, `StatusBadge`, `SummaryCard`, `MinutesView`, `ActionItemList`, `TranscriptView`
(every segment carries `id="segment-<id>"` so Week 2 can scroll to it), `EvidencePanel` (Week 1
placeholder: shows the sentence's evidence ids from the payload and highlights those transcript lines;
entailment bars arrive in Week 3).

## How to run / verify

```powershell
cd frontend
npm ci
npm run typecheck; npm run lint; npm run build      # the same three checks CI runs

npm run mock                                         # terminal 1 — mock API on :4000
$env:NEXT_PUBLIC_API_URL="http://localhost:4000"; npm run dev   # terminal 2 — http://localhost:3000
```

Any email and an 8+ character password logs in on the mock. Against the real backend, run it on
`:8000` and keep the frontend on `:3000` — that is the backend's only CORS origin.

## Numbers

No benchmark numbers this week by design — the frontend produces none.

| Item | Value |
|---|---|
| Routes built | 7 (`/`, `login`, `register`, `dashboard`, `summariser`, `meetings/[id]`, `404`) |
| Components | 10 |
| API functions | 10 — one per §3 endpoint |
| Mock meetings | 3 (done · summarizing · failed) |
| Screenshots | 4 in `demo/screenshots/W1_*.png` |

## Status — verified by running, not by inspection

- ✅ **`tsc --noEmit`, `eslint` and `next build` pass**; all 7 routes prerender.
- ✅ **Every flow driven in headless Chrome against the mock**: redirect to login, wrong-password
  error, dashboard list, minutes tab → evidence lines highlighted, the failed meeting's reason, an
  unsupported file type rejected, upload → stages advance → minutes appear, logout. No horizontal
  overflow at 400 px.
- ✅ **Contract checked against Mounika's real backend** (throwaway database): CORS preflight from
  `localhost:3000`, the 422 validation message, register, upload, list, detail and status all match
  `types.ts` field for field; an unreadable file ends in `failed` with
  `audio failed: the file could not be read as audio`.
- ✅ Merges into `dev` with no conflicts, alone and after the other two Week 1 branches.
- ⬜ **The three sample meetings for `demo/sample_audio/` (Day 0.5) are not recorded.** This one is
  mine, and it blocks Mounika's ASR timing and the Gate 1 demo.
- ⬜ **PR #1 targets `main`.** Weekly PRs go to `dev` (GIT_RULES §6). Against `main` it shows false
  conflicts, because GitHub's `main` still has the pre-cleanup history. Retarget it to `dev`.
- ⬜ Gate 1 end to end with real audio — waits on the recordings, the pyannote download and Lahari's
  checkpoint.

### Lessons worth keeping

- `create-next-app` drops two tool-configuration markdown files into a new app.
  GIT_RULES §0 forbids them, and they were never committed. Check a generator's output before `git add`.
- The generated `frontend/.gitignore` ignores `.env*`, which silently swallowed `.env.example`. It
  now re-includes `!.env.example`.

## Next (Week 2 — `week2-krishna-dialogue-acts`)

- MRDA dialogue-act tagger (DistilRoBERTa on Kaggle, TF-IDF + LR baseline), wired into the pipeline.
- Rule-based action items v1 with `source_segment_id`.
- Transcript coloured by dialogue act, backchannels collapsed, click an action item → scroll to its line.
