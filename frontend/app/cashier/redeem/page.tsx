"use client";

import { useState } from "react";
import Topbar from "@/components/Topbar";
import TokenPanel from "@/components/TokenPanel";
import { apiFetch } from "@/lib/api";

type Stamp = {
  id: number;
  number: number;
  reward_type: string;
  redeemed_at: string | null;
};

type Cycle = {
  id: number;
  cycle_number: number;
  stamps: Stamp[];
};

type Membership = {
  id: number;
  card_number: string;
  customer: { name: string };
  cycles: Cycle[];
};

const rewardLabels: Record<string, string> = {
  free_drink: "Free Drink",
  voucher_50k: "Voucher 50K"
};

export default function RedeemPage() {
  const [identifier, setIdentifier] = useState("");
  const [membership, setMembership] = useState<Membership | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedReward, setSelectedReward] = useState<string>("");

  const handleLookup = async () => {
    setLoading(true);
    setMessage(null);
    setMembership(null);
    setSelectedReward("");
    try {
      const data = await apiFetch<Membership>(
        `/memberships/lookup?q=${encodeURIComponent(identifier)}`
      );
      setMembership(data);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Lookup gagal");
    } finally {
      setLoading(false);
    }
  };

  const handleRedeem = async () => {
    if (!membership || !selectedReward) {
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      await apiFetch(`/memberships/${membership.id}/redeem/`, {
        method: "POST",
        body: JSON.stringify({ reward_type: selectedReward })
      });
      setMessage("Reward berhasil diredeem.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Redeem gagal");
    } finally {
      setLoading(false);
    }
  };

  const availableRewards = membership
    ? membership.cycles
        .flatMap((cycle) => cycle.stamps)
        .filter((stamp) => stamp.reward_type !== "none" && !stamp.redeemed_at)
    : [];

  return (
    <main className="space-y-8">
      <Topbar title="Redeem Reward" subtitle="Tukarkan reward untuk member." />

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Lookup Member</h2>
          <p className="mt-2 text-sm text-slate-300">Gunakan kartu atau nomor HP.</p>
          <div className="mt-4 flex flex-col gap-3">
            <input
              className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
              placeholder="CARD-001 atau 08xxxx"
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
            />
            <button
              className="rounded-xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-900"
              type="button"
              onClick={handleLookup}
              disabled={!identifier || loading}
            >
              {loading ? "Searching..." : "Lookup"}
            </button>
            {message && <p className="text-xs text-slate-300">{message}</p>}
          </div>
        </div>

        <TokenPanel />
      </section>

      <section>
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Available Rewards</h2>
          {!membership && <p className="mt-2 text-sm text-slate-300">No member loaded.</p>}
          {membership && (
            <>
              <p className="mt-2 text-sm text-slate-300">Member: {membership.customer.name}</p>
              <div className="mt-4 flex flex-col gap-3">
                <select
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white"
                  value={selectedReward}
                  onChange={(event) => setSelectedReward(event.target.value)}
                >
                  <option value="">Select reward</option>
                  {availableRewards.map((reward) => (
                    <option key={reward.id} value={reward.reward_type}>
                      {rewardLabels[reward.reward_type] || reward.reward_type} (Stamp #{reward.number})
                    </option>
                  ))}
                </select>
                <button
                  className="rounded-xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-900"
                  type="button"
                  onClick={handleRedeem}
                  disabled={!selectedReward || loading}
                >
                  {loading ? "Processing..." : "Redeem"}
                </button>
              </div>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
