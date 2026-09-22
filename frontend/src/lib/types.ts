// Mirrors the API contract in PROJECT_PLAN.md §3 and backend/app/schemas.py.
// Nullable fields stay null until the pipeline stage that fills them has run.

export const MEETING_STATUSES = [
  "uploaded",
  "transcribing",
  "diarizing",
  "summarizing",
  "tagging",
  "linking",
  "done",
  "failed",
] as const;

export type MeetingStatus = (typeof MEETING_STATUSES)[number];

// Stages the pipeline walks through, in order, between "uploaded" and "done"
export const PIPELINE_STAGES: MeetingStatus[] = [
  "transcribing",
  "diarizing",
  "summarizing",
  "tagging",
  "linking",
];

export type MinuteSection = "decisions" | "actions" | "problems";

export interface TokenResponse {
  token: string;
}

export interface RegisterBody {
  email: string;
  password: string;
  name: string;
}

export interface LoginBody {
  email: string;
  password: string;
}

export interface UploadResponse {
  meeting_id: number;
  status: MeetingStatus;
}

export interface MeetingListItem {
  id: number;
  title: string;
  created_at: string;
  status: MeetingStatus;
  summary_snippet: string | null;
}

export interface Segment {
  id: number;
  speaker: string;
  start_sec: number;
  end_sec: number;
  text: string;
  dialogue_act: string | null;
}

export interface MinuteItem {
  id: number;
  text: string;
  evidence: number[];
  entailment: number | null;
  supported: boolean | null;
}

export interface Minutes {
  decisions: MinuteItem[];
  actions: MinuteItem[];
  problems: MinuteItem[];
}

export interface ActionItem {
  text: string;
  owner: string | null;
  due: string | null;
  source_segment_id: number | null;
  confidence: number | null;
}

export interface Faithfulness {
  score: number | null;
  unsupported_count: number;
}

export interface MeetingDetail {
  id: number;
  title: string;
  status: MeetingStatus;
  participants: string[];
  summary: string | null;
  minutes: Minutes;
  segments: Segment[];
  action_items: ActionItem[];
  faithfulness: Faithfulness;
}

export interface Evidence {
  segment_id: number;
  speaker: string;
  text: string;
  entailment: number;
}

export interface MeetingStatusResponse {
  status: MeetingStatus;
  // current stage while running, the error reason when failed, null otherwise
  stage: string | null;
  elapsed_sec: number;
}

export interface SearchHit {
  meeting_id: number;
  title: string;
  segment_id: number;
  speaker: string;
  text: string;
  score: number;
}

export type ExportFormat = "txt" | "docx";
