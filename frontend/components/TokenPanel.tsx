"use client";

import { useState } from "react";
import { setToken, getToken } from "@/lib/api";

export default function TokenPanel() {
  const [value, setValue] = useState(getToken() || "");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setToken(value.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 1200);
  };

  return (
    <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
      <h2 className="text-lg font-semibold">Auth Token</h2>
      <p className="mt-2 text-sm text-slate-300">Paste JWT token for API requests.</p>
      <div className="mt-4 flex flex-col gap-3">
        <input
          className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
          placeholder="Bearer token"
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
        <button
          className="rounded-xl border border-teal-400/40 bg-teal-400/10 px-4 py-3 text-sm font-semibold text-teal-200"
          type="button"
          onClick={handleSave}
        >
          {saved ? "Saved" : "Save Token"}
        </button>
      </div>
    </div>
  );
}
