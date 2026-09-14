import type { Faithfulness } from "@/lib/types";

interface Props {
  summary: string | null;
  participants: string[];
  faithfulness: Faithfulness;
  pending: boolean;
}

export default function SummaryCard({ summary, participants, faithfulness, pending }: Props) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-semibold">Summary</h2>
        {faithfulness.score !== null && (
          <span className="text-xs text-slate-600">
            faithfulness {faithfulness.score.toFixed(2)}
            {faithfulness.unsupported_count > 0 && (
              <span className="ml-2 text-amber-700">{faithfulness.unsupported_count} unsupported</span>
            )}
          </span>
        )}
      </div>
      {summary ? (
        <p className="mt-2 leading-relaxed text-slate-800">{summary}</p>
      ) : (
        <p className="mt-2 text-sm text-slate-500">
          {pending ? "The summary appears when processing finishes." : "No summary was produced."}
        </p>
      )}
      {participants.length > 0 && (
        <p className="mt-3 text-xs text-slate-500">Participants: {participants.join(", ")}</p>
      )}
    </section>
  );
}
