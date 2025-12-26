"use client";

import { useState } from "react";
import Topbar from "@/components/Topbar";

export default function MembersSearchPage() {
  const [identifier, setIdentifier] = useState("");
  const target = identifier ? `/cashier/members/${encodeURIComponent(identifier)}` : "#";

  return (
    <main className="space-y-8">
      <Topbar title="Member Lookup" subtitle="Cari member via kartu atau nomor HP." />

      <section className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
        <div className="flex flex-col gap-3">
          <label className="text-xs uppercase tracking-wide text-slate-400">
            Card Number / Phone / Public ID
          </label>
          <input
            className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
            placeholder="CARD-001 atau 08xxxx"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
          />
          <a
            className="inline-flex w-fit items-center rounded-xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-900"
            href={target}
          >
            Open Member
          </a>
        </div>
      </section>
    </main>
  );
}
