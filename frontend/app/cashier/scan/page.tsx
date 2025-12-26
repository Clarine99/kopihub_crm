"use client";

import { useState } from "react";
import Topbar from "@/components/Topbar";
import TokenPanel from "@/components/TokenPanel";
import { apiFetch } from "@/lib/api";

type Membership = {
  id: number;
  card_number: string;
  status: string;
  start_date: string;
  end_date: string;
  customer: { name: string; phone: string; email?: string | null };
  cycles?: Array<{ id: number; cycle_number: number; is_closed: boolean; stamps: Array<{ id: number; number: number }> }>;
};

export default function ScanPage() {
  const [publicId, setPublicId] = useState("");
  const [result, setResult] = useState<Membership | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiFetch<Membership>(
        `/memberships/scan/?public_id=${encodeURIComponent(publicId)}`
      );
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="space-y-8">
      <Topbar title="Scan QR" subtitle="Lookup member detail by public_id QR." />

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Scan Input</h2>
          <p className="mt-2 text-sm text-slate-300">Paste the public_id from the QR scanner.</p>
          <div className="mt-4 flex flex-col gap-3">
            <input
              className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
              placeholder="public_id (UUID)"
              value={publicId}
              onChange={(event) => setPublicId(event.target.value)}
            />
            <button
              className="rounded-xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-900"
              type="button"
              onClick={handleScan}
              disabled={!publicId || loading}
            >
              {loading ? "Scanning..." : "Scan"}
            </button>
            {error && <p className="text-xs text-red-300">{error}</p>}
          </div>
        </div>

        <TokenPanel />
      </section>

      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Result</h3>
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          {!result && <p className="text-sm text-slate-300">No data yet.</p>}
          {result && (
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <h2 className="text-xl font-semibold">{result.customer.name}</h2>
                <p className="text-sm text-slate-300">{result.customer.phone}</p>
                <p className="text-sm text-slate-300">{result.customer.email || "No email"}</p>
                <div className="mt-3 inline-flex items-center rounded-full bg-teal-400/20 px-3 py-1 text-xs text-teal-200">
                  {result.status}
                </div>
              </div>
              <div className="space-y-2 text-sm text-slate-300">
                <p>Card: {result.card_number}</p>
                <p>Period: {result.start_date} to {result.end_date}</p>
                <p>Cycles: {result.cycles ? result.cycles.length : 0}</p>
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
