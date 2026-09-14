import { useRouter } from "next/router";
import { useState, type FormEvent } from "react";

import Layout from "@/components/Layout";
import Recorder, { type Recording } from "@/components/Recorder";
import UploadAudio from "@/components/UploadAudio";
import { uploadMeeting } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";

type Source = "upload" | "record";

export default function SummariserPage() {
  const authed = useRequireAuth();
  const router = useRouter();
  const [source, setSource] = useState<Source>("upload");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [recording, setRecording] = useState<Recording | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!authed) return null;

  const ready = title.trim().length > 0 && (source === "upload" ? file !== null : recording !== null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const { meeting_id } =
        source === "upload" && file
          ? await uploadMeeting(file, file.name, title.trim())
          : await uploadMeeting(recording!.blob, recording!.filename, title.trim());
      await router.push(`/meetings/${meeting_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setBusy(false);
    }
  }

  return (
    <Layout title="New meeting">
      <h1 className="text-2xl font-semibold tracking-tight">New meeting</h1>
      <p className="mt-1 text-sm text-slate-600">
        Audio is transcribed, diarised and summarised on this machine. Nothing is sent to a cloud service.
      </p>

      <form onSubmit={submit} className="mt-6 max-w-xl space-y-5">
        <label className="block text-sm font-medium">
          Title
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={200}
            placeholder="e.g. Sprint planning"
            className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </label>

        <div>
          <div className="inline-flex rounded-md border border-slate-300 bg-white p-0.5 text-sm">
            {(["upload", "record"] as const).map((s) => (
              <button
                key={s}
                type="button"
                disabled={busy}
                onClick={() => setSource(s)}
                className={`rounded px-3 py-1.5 ${source === s ? "bg-slate-900 text-white" : "text-slate-600"}`}
              >
                {s === "upload" ? "Upload file" : "Record"}
              </button>
            ))}
          </div>
          <div className="mt-3">
            {source === "upload" ? (
              <UploadAudio file={file} onChange={setFile} disabled={busy} />
            ) : (
              <Recorder recording={recording} onChange={setRecording} disabled={busy} />
            )}
          </div>
        </div>

        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}

        <button
          type="submit"
          disabled={!ready || busy}
          className="rounded-md bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {busy ? "Uploading…" : "Upload and summarise"}
        </button>
      </form>
    </Layout>
  );
}
