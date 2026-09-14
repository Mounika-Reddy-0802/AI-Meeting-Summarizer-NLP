import { useRef, useState } from "react";

// Same list the backend accepts in app/services/audio.py
export const ACCEPTED_EXTENSIONS = [".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac", ".mp4", ".aac", ".opus"];
export const MAX_UPLOAD_MB = 500;

export function checkAudioFile(file: File): string | null {
  const dot = file.name.lastIndexOf(".");
  const ext = dot >= 0 ? file.name.slice(dot).toLowerCase() : "";
  if (!ACCEPTED_EXTENSIONS.includes(ext)) {
    return `Unsupported file type. Use ${ACCEPTED_EXTENSIONS.join(", ")}.`;
  }
  if (file.size === 0) return "The file is empty.";
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `The file is larger than ${MAX_UPLOAD_MB} MB.`;
  return null;
}

export function formatSize(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

interface Props {
  file: File | null;
  onChange: (file: File | null) => void;
  disabled?: boolean;
}

export default function UploadAudio({ file, onChange, disabled }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  function pick(candidate: File | undefined) {
    if (!candidate) return;
    const problem = checkAudioFile(candidate);
    setError(problem);
    onChange(problem ? null : candidate);
  }

  return (
    <div>
      <button
        type="button"
        disabled={disabled}
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!disabled) pick(e.dataTransfer.files[0]);
        }}
        className={`flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-sm transition disabled:opacity-50 ${
          dragging ? "border-indigo-400 bg-indigo-50" : "border-slate-300 bg-white hover:border-slate-400"
        }`}
      >
        {file ? (
          <>
            <span className="font-medium">{file.name}</span>
            <span className="text-slate-500">{formatSize(file.size)} · click to change</span>
          </>
        ) : (
          <>
            <span className="font-medium">Drop an audio file or click to choose</span>
            <span className="text-slate-500">
              wav, mp3, m4a, webm… up to {MAX_UPLOAD_MB} MB and 60 minutes
            </span>
          </>
        )}
      </button>
      <input
        ref={input}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        className="hidden"
        onChange={(e) => {
          pick(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  );
}
