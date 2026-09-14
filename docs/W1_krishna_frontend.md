# W1 — Krishna — frontend

Branch `week1-krishna-frontend` · PROJECT_PLAN.md §5 Krishna tasks 1–7

## What I built

- **App**: Next.js 16 (pages router), TypeScript strict, Tailwind 4, ESLint. `frontend/.env.example`
  has one variable, `NEXT_PUBLIC_API_URL`.
- **Types** (`src/lib/types.ts`): every §3 request/response, including `minutes` with `evidence`,
  `entailment`, `supported`, the `faithfulness` block and the eight status values.
- **API client** (`src/lib/api.ts`): one function per endpoint (register, login, upload, list, get,
  status, evidence, delete, export, search). Adds `Authorization: Bearer`, turns FastAPI `detail`
  (string or validation list) into a readable message, and reports "cannot reach the API" when the
  backend is down.
- **Auth** (`src/lib/auth.tsx`): token in `localStorage`, `useRequireAuth` redirects to
  `/login?next=…`, any 401 logs out.
- **Mock** (`mock/db.json`, `mock/server.cjs`): json-server 0.17 serving the same routes on port 4000 —
  a done meeting with minutes, action items and evidence, one still summarizing, one failed. Uploads
  advance through the five stages every 3 s, so the polling UI can be built without the backend.
- **Pages**
  - `login`, `register` — one shared form; 8-character password check matches the backend.
  - `dashboard` — meetings newest first with status badges and summary snippet; refreshes every 5 s
    while anything is processing; delete for finished meetings.
  - `summariser` — title + upload (drag/drop, same extension list and 500 MB limit as
    `app/services/audio.py`) or record in the browser.
  - `meetings/[id]` — polls `/status` every 2 s and shows the current stage with elapsed time,
    reloading the meeting when the stage changes; failed meetings show the backend's reason; generic
    summary with faithfulness score, Decisions / Actions / Problems tabs with an "unsupported" badge,
    action items with owner / due / confidence, speaker-grouped transcript with timestamps.
- **Components**: `Layout`, `AuthForm`, `Recorder` (MediaRecorder → webm/ogg/m4a blob with preview →
  `/meetings/upload`), `UploadAudio`, `StatusBadge`, `SummaryCard`, `MinutesView`, `ActionItemList`,
  `TranscriptView` (segments carry `id="segment-<id>"` for W2 scroll-to-line), `EvidencePanel`
  (placeholder: shows the sentence's evidence ids from the meeting payload and highlights those lines;
  entailment bars come in W3).

## How to run

```powershell
cd frontend
npm ci
npm run mock                                   # terminal 1, mock API on :4000
$env:NEXT_PUBLIC_API_URL="http://localhost:4000"; npm run dev   # terminal 2, http://localhost:3000
```

Against the real backend: start it on :8000 (see `docs/W1_mounika_local_asr_backend.md`), leave
`NEXT_PUBLIC_API_URL=http://localhost:8000`, run on port 3000 (the backend's CORS origin).

Checks, same as CI: `npm run typecheck`, `npm run lint`, `npm run build`.

## What I verified

- `tsc --noEmit`, `eslint` and `next build` pass (all 7 routes prerender).
- Headless Chrome against the mock: redirect to login, wrong-password error, dashboard list, minutes
  tab → evidence lines highlighted, failed-meeting reason, unsupported file rejected, upload → stages
  advance → minutes appear, logout. No horizontal overflow at 400 px width.
- Against Mounika's backend (`week1-mounika-local-asr-backend`, throwaway database): CORS preflight
  from `localhost:3000`, 422 validation message, register, upload, list, detail and status responses
  match `types.ts` field for field; an unreadable file ends in `failed` with
  `audio failed: the file could not be read as audio`.

Screenshots: `demo/screenshots/W1_upload.png`, `W1_processing.png`, `W1_meeting.png`, `W1_dashboard.png`.

## Numbers

None this week — the frontend produces no benchmark numbers.

## Not done / next

- The three sample meetings for `demo/sample_audio/` (Day 0.5) still need to be recorded with the team.
- Gate 1 end-to-end with real audio waits on the backend and the SAMSum checkpoint being merged into `dev`.
- W2 (`week2-krishna-dialogue-acts`): MRDA tagger, rule-based action items, transcript coloured by
  dialogue act, click an action item to scroll to its line.
