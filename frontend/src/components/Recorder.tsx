import { useEffect, useRef, useState } from "react";

import { formatTime } from "./TranscriptView";
import { formatSize } from "./UploadAudio";

export interface Recording {
  blob: Blob;
  filename: string;
  seconds: number;
}

interface Props {
  recording: Recording | null;
  onChange: (recording: Recording | null) => void;
  disabled?: boolean;
}

// Prefer webm/opus; the backend converts any of these to 16 kHz mono wav
function pickMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) ?? "";
}

function extensionFor(mime: string): string {
  if (mime.includes("ogg")) return ".ogg";
  if (mime.includes("mp4")) return ".m4a";
  return ".webm";
}

export default function Recorder({ recording, onChange, disabled }: Props) {
  const [recordingNow, setRecordingNow] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!recording) return;
    const url = URL.createObjectURL(recording.blob);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPreviewUrl(url);
    return () => {
      URL.revokeObjectURL(url);
      setPreviewUrl(null);
    };
  }, [recording]);

  // stop the microphone if the page is left mid-recording
  useEffect(
    () => () => {
      if (timer.current) clearInterval(timer.current);
      recorder.current?.stream.getTracks().forEach((t) => t.stop());
    },
    [],
  );

  async function start() {
    setError(null);
    if (typeof MediaRecorder === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setError("This browser cannot record audio. Upload a file instead.");
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Microphone access was denied.");
      return;
    }

    const mimeType = pickMimeType();
    const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    const chunks: Blob[] = [];
    const started = Date.now();
    rec.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    rec.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      const type = rec.mimeType || mimeType || "audio/webm";
      const blob = new Blob(chunks, { type });
      const stamp = new Date(started).toISOString().slice(0, 19).replace(/[:T]/g, "-");
      onChange({
        blob,
        filename: `recording-${stamp}${extensionFor(type)}`,
        seconds: Math.round((Date.now() - started) / 1000),
      });
    };

    recorder.current = rec;
    onChange(null);
    setSeconds(0);
    rec.start(1000);
    setRecordingNow(true);
    timer.current = setInterval(() => setSeconds(Math.round((Date.now() - started) / 1000)), 500);
  }

  function stop() {
    if (timer.current) clearInterval(timer.current);
    recorder.current?.stop();
    recorder.current = null;
    setRecordingNow(false);
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-3">
        {recordingNow ? (
          <button
            type="button"
            onClick={stop}
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Stop
          </button>
        ) : (
          <button
            type="button"
            onClick={start}
            disabled={disabled}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {recording ? "Record again" : "Start recording"}
          </button>
        )}
        {recordingNow && (
          <span className="flex items-center gap-2 text-sm text-red-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-600" aria-hidden />
            Recording {formatTime(seconds)}
          </span>
        )}
        {recording && !recordingNow && (
          <span className="text-sm text-slate-600">
            {formatTime(recording.seconds)} recorded · {formatSize(recording.blob.size)}
          </span>
        )}
      </div>
      {previewUrl && !recordingNow && <audio controls src={previewUrl} className="mt-3 w-full" />}
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  );
}
