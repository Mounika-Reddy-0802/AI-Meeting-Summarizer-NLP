# frontend/

Krishna - Next.js (pages router) + TypeScript (strict) + Tailwind client for the offline meeting summarizer.

## Run

```powershell
cd frontend
npm ci
copy .env.example .env.local      # NEXT_PUBLIC_API_URL, the only variable
npm run dev                        # http://localhost:3000
```

The backend allows CORS from `http://localhost:3000` only, so keep that port when pointing at it.

### Without the backend (json-server mock)

```powershell
npm run mock                       # mock API on http://localhost:4000
$env:NEXT_PUBLIC_API_URL="http://localhost:4000"; npm run dev
```

`mock/db.json` holds three meetings (done, still summarizing, failed). Any email with a password of 8+
characters logs in. An upload walks through the pipeline stages, 3 s each, then shows the sample minutes.

## Checks (same as CI)

```powershell
npm run typecheck                  # tsc --noEmit
npm run lint
npm run build
```

## Layout

| Path | What |
|------|------|
| `src/lib/types.ts` | Types mirroring the API contract (PROJECT_PLAN.md §3) |
| `src/lib/api.ts` | `fetch` wrapper that adds the JWT; one function per endpoint |
| `src/lib/auth.tsx` | `AuthProvider`, `useAuth`, `useRequireAuth`; token in `localStorage`, logout on 401 |
| `src/pages/` | `login`, `register`, `dashboard`, `summariser`, `meetings/[id]` |
| `src/components/` | `Layout`, `AuthForm`, `Recorder`, `UploadAudio`, `StatusBadge`, `SummaryCard`, `MinutesView`, `ActionItemList`, `TranscriptView`, `EvidencePanel` (placeholder until W3) |
| `mock/` | `db.json` + `server.cjs` (json-server 0.17) |
