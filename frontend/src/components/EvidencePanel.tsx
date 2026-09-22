import type { MinuteItem, Segment } from "@/lib/types";

interface Props {
  item: MinuteItem | null;
  segments: Segment[];
}

// Week 1 placeholder: shows the evidence ids already in the meeting payload.
// TODO(W3): fetch /meetings/{id}/evidence and draw entailment bars per supporting turn.
export default function EvidencePanel({ item, segments }: Props) {
  if (!item) {
    return (
      <aside className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
        Select a minute sentence to see the transcript turns that support it.
      </aside>
    );
  }

  const linked = item.evidence
    .map((id) => segments.find((s) => s.id === id))
    .filter((s): s is Segment => s !== undefined);

  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-5 text-sm">
      <h3 className="font-semibold">Evidence</h3>
      <p className="mt-1 text-slate-700">&ldquo;{item.text}&rdquo;</p>
      {item.entailment !== null && (
        <p className="mt-1 text-xs text-slate-500">entailment {item.entailment.toFixed(2)}</p>
      )}
      {linked.length === 0 ? (
        <p className="mt-3 text-slate-500">Evidence linking is not available for this sentence yet.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {linked.map((seg) => (
            <li key={seg.id} className="rounded-md bg-slate-50 px-3 py-2">
              <span className="font-medium">{seg.speaker}:</span> {seg.text}
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
