/**
 * Auth route group layout.
 * Focused Generic AQAA authentication surface — no application chrome.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#f6f7f4] px-4 py-10 text-[#171815]">
      <div className="absolute left-1/2 top-[-18rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-[#dce8e1] blur-3xl" aria-hidden="true" />
      <div className="relative mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl items-center justify-center">
        {children}
      </div>
    </div>
  );
}
