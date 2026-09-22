import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

import ActionItemList from "@/components/ActionItemList";
import EvidencePanel from "@/components/EvidencePanel";
import Layout from "@/components/Layout";
import MinutesView from "@/components/MinutesView";
import StatusBadge, { isRunning } from "@/components/StatusBadge";
import SummaryCard from "@/components/SummaryCard";
import TranscriptView, { formatTime } from "@/components/TranscriptView";
import { ApiError, getMeeting, getMeetingStatus } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import { PIPELINE_STAGES, type MeetingDetail, type MeetingStatusResponse, type MinuteItem } from "@/lib/types";

const POLL_MS = 2000;

function StageProgress({ status }: { status: MeetingStatusResponse }) {
  const current = PIPELINE_STAGES.indexOf(status.status);
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-semibold">Processing</h2>
        <span className="font-mono text-xs text-slate-500">{formatTime(status.elapsed_sec)} elapsed</span>
      </div>
      <ol className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
        {PIPELINE_STAGES.map((stage, i) => {
          const state = current < 0 ? "todo" : i < current ? "done" : i === current ? "active" : "todo";
          return (
            <li
              key={stage}
              className={`rounded-md border px-3 py-2 text-xs ${
                state === "done"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : state === "active"
                    ? "border-indigo-300 bg-indigo-50 font-medium text-indigo-800"
                    : "border-slate-200 text-slate-400"
              }`}
            >
              {state === "active" && <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
              {stage}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

export default function MeetingPage() {
  const authed = useRequireAuth();
  const router = useRouter();
  const id = Number(router.query.id);
  const validId = router.isReady && Number.isInteger(id) && id > 0;

  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [status, setStatus] = useState<MeetingStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<MinuteItem | null>(null);

  const load = useCallback(async () => {
    try {
      const [detail, stat] = await Promise.all([getMeeting(id), getMeetingStatus(id)]);
      setMeeting(detail);
      setStatus(stat);
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 404
          ? "Meeting not found."
          : err instanceof Error
            ? err.message
            : "Could not load the meeting.",
      );
    }
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (authed && validId) void load();
  }, [authed, validId, load]);

  // Poll /status while the pipeline runs; reload the full meeting whenever the stage changes
  const running = status ? isRunning(status.status) : false;
  useEffect(() => {
    if (!running) return;
    let last = status?.status;
    const timer = setInterval(async () => {
      try {
        const next = await getMeetingStatus(id);
        setStatus(next);
        if (next.status !== last) {
          last = next.status;
          setMeeting(await getMeeting(id));
        }
      } catch {
        // transient; the next tick retries
      }
    }, POLL_MS);
    return () => clearInterval(timer);
    // status is read once to seed `last`; re-running on every tick would reset the interval
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, id]);

  if (!authed) return null;

  return (
    <Layout title={meeting?.title ?? "Meeting"}>
      <Link href="/dashboard" className="text-sm text-slate-600 hover:underline">
        ← All meetings
      </Link>

      {error && <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
      {!meeting && !error && <p className="mt-6 text-sm text-slate-500">Loading…</p>}

      {meeting && status && (
        <div className="mt-3 space-y-5">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{meeting.title}</h1>
            <StatusBadge status={status.status} />
          </div>

          {running && <StageProgress status={status} />}

          {status.status === "failed" && (
            <section className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-900">
              <h2 className="font-semibold">Processing failed</h2>
              <p className="mt-1">{status.stage ?? "The pipeline stopped with an unknown error."}</p>
              <Link href="/summariser" className="mt-2 inline-block font-medium underline">
                Try another file
              </Link>
            </section>
          )}

          <SummaryCard
            summary={meeting.summary}
            participants={meeting.participants}
            faithfulness={meeting.faithfulness}
            pending={running}
          />

          <div className="grid gap-5 lg:grid-cols-[1fr_20rem]">
            <MinutesView minutes={meeting.minutes} selectedId={selected?.id ?? null} onSelect={setSelected} />
            <EvidencePanel item={selected} segments={meeting.segments} />
          </div>

          <ActionItemList items={meeting.action_items} />

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="mb-4 font-semibold">Transcript</h2>
            <TranscriptView segments={meeting.segments} highlightIds={selected?.evidence} />
          </section>
        </div>
      )}
    </Layout>
  );
}
