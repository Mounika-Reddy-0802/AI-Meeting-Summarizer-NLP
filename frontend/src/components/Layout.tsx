import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import type { ReactNode } from "react";

import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Meetings" },
  { href: "/summariser", label: "New meeting" },
];

export default function Layout({ title, children }: { title?: string; children: ReactNode }) {
  const { token, logout } = useAuth();
  const router = useRouter();
  const pageTitle = title ? `${title} · Meeting Summarizer` : "Meeting Summarizer";

  return (
    <>
      <Head>
        <title>{pageTitle}</title>
      </Head>
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
            <Link href={token ? "/dashboard" : "/login"} className="font-semibold tracking-tight">
              Meeting Summarizer
              <span className="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-xs font-medium text-emerald-800">
                offline
              </span>
            </Link>
            {token && (
              <nav className="flex items-center gap-1 text-sm">
                {NAV.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded px-3 py-1.5 hover:bg-slate-100 ${
                      router.pathname === item.href ? "bg-slate-100 font-medium" : "text-slate-600"
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
                <button
                  type="button"
                  onClick={logout}
                  className="rounded px-3 py-1.5 text-slate-600 hover:bg-slate-100"
                >
                  Log out
                </button>
              </nav>
            )}
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
      </div>
    </>
  );
}
