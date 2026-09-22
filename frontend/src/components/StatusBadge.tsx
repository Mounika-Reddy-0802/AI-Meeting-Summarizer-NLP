import type { MeetingStatus } from "@/lib/types";

const STYLES: Record<MeetingStatus, string> = {
  uploaded: "bg-slate-100 text-slate-700",
  transcribing: "bg-sky-100 text-sky-800",
  diarizing: "bg-sky-100 text-sky-800",
  summarizing: "bg-indigo-100 text-indigo-800",
  tagging: "bg-indigo-100 text-indigo-800",
  linking: "bg-violet-100 text-violet-800",
  done: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
};

export function isRunning(status: MeetingStatus): boolean {
  return status !== "done" && status !== "failed";
}

export default function StatusBadge({ status }: { status: MeetingStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {isRunning(status) && (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" aria-hidden />
      )}
      {status}
    </span>
  );
}
