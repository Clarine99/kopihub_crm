import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "KopiHub CRM",
  description: "Cashier tools for membership and rewards"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="min-h-screen px-6 py-8 lg:px-12">{children}</div>
      </body>
    </html>
  );
}
