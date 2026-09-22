import { useState } from "react";

import type { MinuteItem, MinuteSection, Minutes } from "@/lib/types";

const TABS: { key: MinuteSection; label: string }[] = [
  { key: "decisions", label: "Decisions" },
  { key: "actions", label: "Actions" },
  { key: "problems", label: "Problems" },
];

interface Props {
  minutes: Minutes;
  selectedId: number | null;
  onSelect: (item: MinuteItem | null) => void;
}

export default function MinutesView({ minutes, selectedId, onSelect }: Props) {
  const [tab, setTab] = useState<MinuteSection>("decisions");
  const items = minutes[tab];

  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div role="tablist" className="flex border-b border-slate-200 px-2">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            role="tab"
            type="button"
            aria-selected={tab === key}
            onClick={() => {
              setTab(key);
              onSelect(null);
            }}
            className={`-mb-px border-b-2 px-3 py-2.5 text-sm ${
              tab === key
                ? "border-indigo-600 font-medium text-indigo-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            {label}
            <span className="ml-1.5 rounded-full bg-slate-100 px-1.5 text-xs text-slate-600">
              {minutes[key].length}
            </span>
          </button>
        ))}
      </div>

      {items.length === 0 ? (
        <p className="p-5 text-sm text-slate-500">Nothing in this section yet.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onSelect(selectedId === item.id ? null : item)}
                className={`flex w-full items-start gap-3 px-5 py-3 text-left text-sm hover:bg-slate-50 ${
                  selectedId === item.id ? "bg-indigo-50" : ""
                }`}
              >
                <span className="flex-1 leading-relaxed">{item.text}</span>
                {item.supported === false && (
                  <span className="shrink-0 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800">
                    unsupported
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
