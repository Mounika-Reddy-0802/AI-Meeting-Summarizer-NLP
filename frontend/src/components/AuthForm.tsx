import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState, type FormEvent } from "react";

import Layout from "./Layout";
import { useAuth } from "@/lib/auth";

// Shared by /login and /register; register also asks for a name
export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { token, ready, login, register } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isRegister = mode === "register";
  const next = typeof router.query.next === "string" && router.query.next.startsWith("/")
    ? router.query.next
    : "/dashboard";

  useEffect(() => {
    if (ready && token) void router.replace(next);
  }, [ready, token, next, router]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (isRegister && password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      if (isRegister) await register({ name: name.trim(), email: email.trim(), password });
      else await login({ email: email.trim(), password });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const input =
    "mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

  return (
    <Layout title={isRegister ? "Create account" : "Log in"}>
      <div className="mx-auto mt-10 max-w-sm rounded-lg border border-slate-200 bg-white p-6">
        <h1 className="text-xl font-semibold">{isRegister ? "Create an account" : "Log in"}</h1>
        <p className="mt-1 text-sm text-slate-500">
          Audio and transcripts stay on this machine.
        </p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          {isRegister && (
            <label className="block text-sm font-medium">
              Name
              <input className={input} value={name} onChange={(e) => setName(e.target.value)} required maxLength={100} autoComplete="name" />
            </label>
          )}
          <label className="block text-sm font-medium">
            Email
            <input className={input} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input
              className={input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={isRegister ? 8 : undefined}
              maxLength={128}
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
          </label>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {busy ? "Please wait…" : isRegister ? "Create account" : "Log in"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-600">
          {isRegister ? "Already have an account? " : "No account yet? "}
          <Link href={isRegister ? "/login" : "/register"} className="font-medium text-indigo-700 hover:underline">
            {isRegister ? "Log in" : "Create one"}
          </Link>
        </p>
      </div>
    </Layout>
  );
}
