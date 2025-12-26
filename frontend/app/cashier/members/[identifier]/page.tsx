"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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
  is_closed: boolean;
  stamps: Stamp[];
};

type Membership = {
  id: number;
  card_number: string;
  status: string;
  start_date: string;
  end_date: string;
  customer: { name: string; phone: string };
  cycles: Cycle[];
};

export default function MemberDetailPage() {
  const params = useParams<{ identifier: string }>();
  const [data, setData] = useState<Membership | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const membership = await apiFetch<Membership>(
          `/memberships/lookup?q=${encodeURIComponent(params.identifier)}`
        );
        setData(membership);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Member tidak ditemukan");
      }
    };

    if (params.identifier) {
      load();
    }
  }, [params.identifier]);

  const latestCycle = data?.cycles?.[data.cycles.length - 1];
  const stampCount = latestCycle?.stamps.length ?? 0;
  const rewards = data
    ? data.cycles.flatMap((cycle) => cycle.stamps).filter((stamp) => stamp.reward_type !== "none")
    : [];

  return (
    <main className="space-y-8">
      <Topbar title="Member Detail" subtitle="Ringkasan status member." />

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          {error && <p className="text-xs text-red-300">{error}</p>}
          {!data && !error && <p className="text-sm text-slate-300">Memuat...</p>}
          {data && (
            <>
              <h2 className="text-xl font-semibold">{data.customer.name}</h2>
              <p className="text-sm text-slate-300">{data.customer.phone}</p>
              <p className="text-sm text-slate-300">Card: {data.card_number}</p>
              <div className="mt-3 inline-flex items-center rounded-full bg-teal-400/20 px-3 py-1 text-xs text-teal-200">
                {data.status}
              </div>
              <p className="mt-3 text-sm text-slate-300">
                Period: {data.start_date} to {data.end_date}
              </p>
            </>
          )}
        </div>
        <TokenPanel />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Current Cycle</h2>
          <p className="text-sm text-slate-300">Cycle #{latestCycle?.cycle_number ?? "-"}</p>
          <p className="text-sm text-slate-300">Stamp count: {stampCount}/10</p>
        </div>
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Rewards</h2>
          {!rewards.length && <p className="text-sm text-slate-300">No rewards yet.</p>}
          {rewards.map((reward) => (
            <p key={reward.id} className="text-sm text-slate-300">
              Stamp #{reward.number} - {reward.reward_type} - {reward.redeemed_at ? "Redeemed" : "Available"}
            </p>
          ))}
        </div>
      </section>
    </main>
  );
}
