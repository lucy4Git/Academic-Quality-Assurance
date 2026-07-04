/**
 * Auth route group layout.
 * Centred card on a navy gradient background — no sidebar, no topbar.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1E3A5F] via-[#1a3258] to-[#0f2340] p-4">
      {children}
    </div>
  );
}
