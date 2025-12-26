const links = [
  { href: "/", label: "Home" },
  { href: "/cashier/scan", label: "Scan QR" },
  { href: "/cashier/members", label: "Lookup" },
  { href: "/cashier/add-stamp", label: "Add Stamp" },
  { href: "/cashier/redeem", label: "Redeem" }
];

export default function Topbar({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="text-sm text-slate-300">{subtitle}</p>
      </div>
      <nav className="flex flex-wrap gap-3">
        {links.map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs text-slate-300 transition hover:border-amber-400 hover:text-white"
          >
            {link.label}
          </a>
        ))}
      </nav>
    </div>
  );
}
