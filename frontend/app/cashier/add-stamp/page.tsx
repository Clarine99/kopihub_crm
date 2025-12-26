"use client";

import { useState } from "react";
import Topbar from "@/components/Topbar";
import TokenPanel from "@/components/TokenPanel";
import { apiFetch } from "@/lib/api";

type Membership = { id: number; customer: { name: string }; card_number: string };

type Stamp = {
  id: number;
  number: number;
  reward_type: string;
  cycle: number;
};

export default function AddStampPage() {
  const [identifier, setIdentifier] = useState("");
  const [amount, setAmount] = useState("");
  const [receipt, setReceipt] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const membership = await apiFetch<Membership>(
        `/memberships/lookup?q=${encodeURIComponent(identifier)}`
      );
      const stamp = await apiFetch<Stamp>(`/memberships/${membership.id}/add-stamp/`, {
        method: "POST",
        body: JSON.stringify({
          transaction_amount: amount,
          pos_receipt_number: receipt || null
        })
      });

      if ((stamp as unknown as { detail?: string }).detail === "No stamp awarded") {
        setMessage("Transaksi tidak memenuhi syarat stamp.");
      } else {
        setMessage(`Stamp #${stamp.number} diberikan. Reward: ${stamp.reward_type}.`);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Gagal menambah stamp");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="space-y-8">
      <Topbar title="Add Stamp" subtitle="Input transaksi untuk menambah stamp." />

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Stamp Form</h2>
          <p className="mt-2 text-sm text-slate-300">
            Gunakan kartu atau nomor HP untuk lookup member.
          </p>
          <div className="mt-4 flex flex-col gap-3">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Card Number / Phone</label>
              <input
                className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
                placeholder="CARD-001 atau 08xxxx"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Transaction Amount</label>
              <input
                className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
                type="number"
                placeholder="75000"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">POS Receipt Number</label>
              <input
                className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
                placeholder="STRUK-123"
                value={receipt}
                onChange={(event) => setReceipt(event.target.value)}
              />
            </div>
            <button
              className="rounded-xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-900"
              type="button"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? "Saving..." : "Add Stamp"}
            </button>
            {message && <p className="text-xs text-slate-300">{message}</p>}
          </div>
        </div>

        <TokenPanel />
      </section>
    </main>
  );
}
