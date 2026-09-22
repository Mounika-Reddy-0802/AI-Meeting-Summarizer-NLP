// Mock of the §3 API on json-server, so the UI can be built without the backend.
// Run: npm run mock  (port 4000). Data comes from db.json; nothing is written back to it.

const path = require("path");
const jsonServer = require("json-server");

const PORT = Number(process.env.MOCK_PORT || 4000);
const STAGES = ["transcribing", "diarizing", "summarizing", "tagging", "linking"];
const SECONDS_PER_STAGE = 3;

const server = jsonServer.create();
const router = jsonServer.router(path.join(__dirname, "db.json"), { foreignKeySuffix: "_none" });
const db = router.db;

server.use(jsonServer.defaults({ noCors: false, logger: true }));
server.use(jsonServer.bodyParser);

// Uploads made while the mock runs: id -> {started, title}. They walk through the stages.
const uploads = new Map();
let nextId = 1000;

function requireToken(req, res, next) {
  if (!/^Bearer .+/.test(req.headers.authorization || "")) {
    return res.status(401).json({ detail: "Not authenticated" });
  }
  next();
}

function uploadState(id) {
  const upload = uploads.get(id);
  const elapsed = (Date.now() - upload.started) / 1000;
  const index = Math.floor(elapsed / SECONDS_PER_STAGE);
  const status = index >= STAGES.length ? "done" : STAGES[index];
  return { status, elapsed };
}

function findMeeting(id) {
  if (uploads.has(id)) {
    const { status } = uploadState(id);
    const template = db.get("meetings").find({ id: 1 }).value();
    const done = status === "done";
    const transcribed = !["transcribing", "diarizing"].includes(status);
    return {
      ...template,
      id,
      title: uploads.get(id).title,
      created_at: new Date(uploads.get(id).started).toISOString(),
      status,
      participants: transcribed ? template.participants : [],
      summary: done ? template.summary : null,
      minutes: done ? template.minutes : { decisions: [], actions: [], problems: [] },
      segments: transcribed ? template.segments : [],
      action_items: done ? template.action_items : [],
      faithfulness: done ? template.faithfulness : { score: null, unsupported_count: 0 },
    };
  }
  return db.get("meetings").find({ id }).value();
}

function allMeetings() {
  const uploaded = [...uploads.keys()].map(findMeeting);
  return [...uploaded.reverse(), ...db.get("meetings").value()];
}

server.post(["/auth/login", "/auth/register"], (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) return res.status(422).json({ detail: "Email and password are required" });
  if (password.length < 8) return res.status(401).json({ detail: "Invalid email or password" });
  res.status(req.path.endsWith("register") ? 201 : 200).json({ token: `mock-token-${Date.now()}` });
});

server.use(["/meetings", "/search"], requireToken);

server.post("/meetings/upload", (req, res) => {
  const id = nextId++;
  // multipart body is not parsed; the title is not needed for the mock flow to work
  uploads.set(id, { started: Date.now(), title: `Uploaded meeting ${id}` });
  res.status(202).json({ meeting_id: id, status: "uploaded" });
});

server.get("/meetings", (_req, res) => {
  res.json(
    allMeetings().map((m) => ({
      id: m.id,
      title: m.title,
      created_at: m.created_at,
      status: m.status,
      summary_snippet: m.summary ? m.summary.slice(0, 160) : null,
    })),
  );
});

server.get("/meetings/:id/status", (req, res) => {
  const id = Number(req.params.id);
  if (uploads.has(id)) {
    const { status, elapsed } = uploadState(id);
    const done = status === "done";
    return res.json({
      status,
      stage: done ? null : status,
      elapsed_sec: Math.round(Math.min(elapsed, STAGES.length * SECONDS_PER_STAGE) * 10) / 10,
    });
  }
  const row = db.get("statuses").find({ id }).value();
  if (!row) return res.status(404).json({ detail: "Meeting not found" });
  res.json({ status: row.status, stage: row.stage, elapsed_sec: row.elapsed_sec });
});

server.get("/meetings/:id/evidence", (req, res) => {
  const rows = db
    .get("evidence")
    .filter({ sentence_id: Number(req.query.sentence_id) })
    .sortBy((r) => -r.entailment)
    .value();
  res.json(rows.map(({ segment_id, speaker, text, entailment }) => ({ segment_id, speaker, text, entailment })));
});

server.get("/meetings/:id", (req, res) => {
  const meeting = findMeeting(Number(req.params.id));
  if (!meeting) return res.status(404).json({ detail: "Meeting not found" });
  res.json(meeting);
});

server.delete("/meetings/:id", (req, res) => {
  const id = Number(req.params.id);
  // lodash chain mutates the in-memory copy only; db.json on disk is never written
  if (!uploads.delete(id)) db.get("meetings").remove({ id }).value();
  res.status(204).end();
});

server.get("/search", (req, res) => {
  const q = String(req.query.q || "").toLowerCase();
  const k = Number(req.query.k || 10);
  const hits = [];
  for (const m of allMeetings()) {
    for (const s of m.segments) {
      if (q && s.text.toLowerCase().includes(q)) {
        hits.push({ meeting_id: m.id, title: m.title, segment_id: s.id, speaker: s.speaker, text: s.text, score: 1 });
      }
    }
  }
  res.json(hits.slice(0, k));
});

server.listen(PORT, () => {
  console.log(`mock API on http://localhost:${PORT} (set NEXT_PUBLIC_API_URL to this)`);
});
