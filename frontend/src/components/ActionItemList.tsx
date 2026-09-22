import type { ActionItem } from "@/lib/types";

export default function ActionItemList({ items }: { items: ActionItem[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="font-semibold">Action items</h2>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No action items found.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {items.map((item, i) => (
            <li
              key={`${item.source_segment_id ?? "x"}-${i}`}
              className="flex flex-wrap items-baseline gap-x-3 gap-y-1 rounded-md bg-slate-50 px-3 py-2 text-sm"
            >
              <span className="flex-1">{item.text}</span>
              <span className="text-xs text-slate-600">
                owner <span className="font-medium text-slate-800">{item.owner ?? "unassigned"}</span>
              </span>
              {item.due && <span className="text-xs text-slate-600">due {item.due}</span>}
              {item.confidence !== null && (
                <span className="text-xs text-slate-400">{Math.round(item.confidence * 100)}%</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
