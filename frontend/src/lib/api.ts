// One function per endpoint in PROJECT_PLAN.md §3. Every call sends the stored JWT.

import type {
  Evidence,
  ExportFormat,
  LoginBody,
  MeetingDetail,
  MeetingListItem,
  MeetingStatusResponse,
  RegisterBody,
  SearchHit,
  TokenResponse,
  UploadResponse,
} from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

const TOKEN_KEY = "ams_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // storage blocked (private mode); the session lasts until reload
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Called when any request comes back 401, so the auth context can log out
let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

// FastAPI sends {detail: "..."} or, for validation errors, {detail: [{msg, loc}]}
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail) && body.detail.length > 0) {
      return body.detail.map((d: { msg?: string }) => d.msg ?? "Invalid input").join("; ");
    }
  } catch {
    // not json
  }
  return res.statusText || `Request failed (${res.status})`;
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, `Cannot reach the API at ${API_URL}. Is the backend running?`);
  }

  if (res.status === 401 && token) onUnauthorized?.();
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res));
  return res;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await request(path, init);
  return (await res.json()) as T;
}

// --- auth ---

export function register(body: RegisterBody): Promise<TokenResponse> {
  return json("/auth/register", { method: "POST", body: JSON.stringify(body) });
}

export function login(body: LoginBody): Promise<TokenResponse> {
  return json("/auth/login", { method: "POST", body: JSON.stringify(body) });
}

// --- meetings ---

export function uploadMeeting(file: Blob, filename: string, title: string): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file, filename);
  form.append("title", title);
  return json("/meetings/upload", { method: "POST", body: form });
}

export function listMeetings(): Promise<MeetingListItem[]> {
  return json("/meetings");
}

export function getMeeting(id: number): Promise<MeetingDetail> {
  return json(`/meetings/${id}`);
}

export function getMeetingStatus(id: number): Promise<MeetingStatusResponse> {
  return json(`/meetings/${id}/status`);
}

export function getEvidence(id: number, sentenceId: number): Promise<Evidence[]> {
  return json(`/meetings/${id}/evidence?sentence_id=${sentenceId}`);
}

export async function deleteMeeting(id: number): Promise<void> {
  await request(`/meetings/${id}`, { method: "DELETE" });
}

export async function exportMeeting(id: number, format: ExportFormat): Promise<Blob> {
  const res = await request(`/meetings/${id}/export?format=${format}`);
  return res.blob();
}

// --- search ---

export function search(q: string, k = 10): Promise<SearchHit[]> {
  return json(`/search?q=${encodeURIComponent(q)}&k=${k}`);
}
