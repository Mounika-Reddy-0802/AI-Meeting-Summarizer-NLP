import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import Layout from "@/components/Layout";
import StatusBadge, { isRunning } from "@/components/StatusBadge";
import { deleteMeeting, listMeetings } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import type { MeetingListItem } from "@/lib/types";

const REFRESH_MS = 5000;

export default function DashboardPage() {
  const authed = useRequireAuth();
  const [meetings, setMeetings] = useState<MeetingListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setMeetings(await listMeetings());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load meetings.");
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (authed) void load();
  }, [authed, load]);

  // keep badges moving while anything is still processing
  const anyRunning = meetings?.some((m) => isRunning(m.status)) ?? false;
  useEffect(() => {
    if (!anyRunning) return;
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [anyRunning, load]);

  async function remove(meeting: MeetingListItem) {
    if (!window.confirm(`Delete "${meeting.title}"? This removes its audio and transcript.`)) return;
    try {
      await deleteMeeting(meeting.id);
      setMeetings((list) => list?.filter((m) => m.id !== meeting.id) ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the meeting.");
    }
  }

  if (!authed) return null;

  return (
    <Layout title="Meetings">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Meetings</h1>
        <Link
          href="/summariser"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          New meeting
        </Link>
      </div>

      {error && <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}

      {meetings === null && !error && <p className="mt-6 text-sm text-slate-500">Loading…</p>}

      {meetings?.length === 0 && (
        <div className="mt-6 rounded-lg border border-dashed border-slate-300 p-10 text-center">
          <p className="font-medium">No meetings yet</p>
          <p className="mt-1 text-sm text-slate-500">Record or upload one to get a transcript and minutes.</p>
        </div>
      )}

      {meetings && meetings.length > 0 && (
        <ul className="mt-6 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {meetings.map((m) => (
            <li key={m.id} className="flex items-start gap-4 px-5 py-4">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Link href={`/meetings/${m.id}`} className="font-medium hover:underline">
                    {m.title}
                  </Link>
                  <StatusBadge status={m.status} />
                </div>
                <p className="mt-0.5 text-xs text-slate-500">{new Date(m.created_at).toLocaleString()}</p>
                {m.summary_snippet && (
                  <p className="mt-1.5 line-clamp-2 text-sm text-slate-700">{m.summary_snippet}</p>
                )}
              </div>
              {!isRunning(m.status) && (
                <button
                  type="button"
                  onClick={() => remove(m)}
                  className="shrink-0 rounded px-2 py-1 text-xs text-slate-500 hover:bg-red-50 hover:text-red-700"
                >
                  Delete
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </Layout>
  );
}
