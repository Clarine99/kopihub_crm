import Link from "next/link";

const links = [
  { href: "/cashier/scan", label: "Scan QR" },
  { href: "/cashier/members", label: "Lookup Member" },
  { href: "/cashier/add-stamp", label: "Add Stamp" },
  { href: "/cashier/redeem", label: "Redeem Reward" }
];

export default function HomePage() {
  return (
    <main className="space-y-10">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">KopiHub Cashier Console</h1>
          <p className="text-sm text-slate-300">
            Fast lookup, stamp, and reward flow.
          </p>
        </div>
        <nav className="flex flex-wrap gap-3">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs text-slate-300 transition hover:border-amber-400 hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>

      <section className="grid gap-6 md:grid-cols-2">
        <Link
          href="/cashier/scan"
          className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel transition hover:border-amber-400"
        >
          <h2 className="text-lg font-semibold">Scan QR</h2>
          <p className="mt-2 text-sm text-slate-300">
            Scan public_id from QR to fetch member detail instantly.
          </p>
        </Link>
        <Link
          href="/cashier/members"
          className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel transition hover:border-amber-400"
        >
          <h2 className="text-lg font-semibold">Lookup Member</h2>
          <p className="mt-2 text-sm text-slate-300">
            Search by card number or phone without QR.
          </p>
        </Link>
        <Link
          href="/cashier/add-stamp"
          className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel transition hover:border-amber-400"
        >
          <h2 className="text-lg font-semibold">Stamp Transaction</h2>
          <p className="mt-2 text-sm text-slate-300">
            Log eligible transactions and auto-advance reward cycles.
          </p>
        </Link>
        <Link
          href="/cashier/redeem"
          className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel transition hover:border-amber-400"
        >
          <h2 className="text-lg font-semibold">Redeem Reward</h2>
          <p className="mt-2 text-sm text-slate-300">
            Redeem free drinks or vouchers with one tap.
          </p>
        </Link>
        <div className="rounded-2xl border border-white/15 bg-white/5 p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Tip</h2>
          <p className="mt-2 text-sm text-slate-300">
            Set NEXT_PUBLIC_API_BASE_URL to your backend URL.
          </p>
        </div>
      </section>
    </main>
  );
}
