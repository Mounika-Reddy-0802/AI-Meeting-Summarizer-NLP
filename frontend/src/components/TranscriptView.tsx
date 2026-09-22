import type { Segment } from "@/lib/types";

export function formatTime(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}

const SPEAKER_COLOURS = [
  "text-indigo-700",
  "text-emerald-700",
  "text-amber-700",
  "text-rose-700",
  "text-sky-700",
  "text-fuchsia-700",
];

interface Turn {
  speaker: string;
  start: number;
  segments: Segment[];
}

// Consecutive segments from the same speaker read as one turn
function groupBySpeaker(segments: Segment[]): Turn[] {
  const turns: Turn[] = [];
  for (const seg of segments) {
    const last = turns[turns.length - 1];
    if (last && last.speaker === seg.speaker) last.segments.push(seg);
    else turns.push({ speaker: seg.speaker, start: seg.start_sec, segments: [seg] });
  }
  return turns;
}

interface Props {
  segments: Segment[];
  highlightIds?: number[];
}

export default function TranscriptView({ segments, highlightIds = [] }: Props) {
  if (segments.length === 0) {
    return <p className="text-sm text-slate-500">No transcript yet.</p>;
  }

  const speakers = [...new Set(segments.map((s) => s.speaker))];
  const colour = (speaker: string) => SPEAKER_COLOURS[speakers.indexOf(speaker) % SPEAKER_COLOURS.length];

  return (
    <ol className="space-y-4">
      {groupBySpeaker(segments).map((turn) => (
        <li key={turn.segments[0].id} className="grid grid-cols-[3.5rem_1fr] gap-3">
          <span className="pt-0.5 text-right font-mono text-xs text-slate-400">{formatTime(turn.start)}</span>
          <div>
            <p className={`text-sm font-semibold ${colour(turn.speaker)}`}>{turn.speaker}</p>
            <p className="text-sm leading-relaxed text-slate-800">
              {turn.segments.map((seg) => (
                <span
                  key={seg.id}
                  id={`segment-${seg.id}`}
                  title={`${formatTime(seg.start_sec)}–${formatTime(seg.end_sec)}`}
                  className={highlightIds.includes(seg.id) ? "rounded bg-amber-100" : undefined}
                >
                  {seg.text}{" "}
                </span>
              ))}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
