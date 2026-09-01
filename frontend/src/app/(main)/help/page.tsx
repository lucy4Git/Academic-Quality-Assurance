import Link from "next/link";

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div><h1 className="text-3xl font-bold">Help</h1><p className="mt-1 text-muted-foreground">Use AQAA with evidence-aware, owner-scoped workflows.</p></div>
      <div className="grid gap-3 sm:grid-cols-2">
        <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Attach evidence</h2><p className="mt-2 text-sm text-muted-foreground">Use the paperclip or drag files onto the composer. Wait for Ready before asking for an evidence-grounded review.</p></section>
        <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Credential review</h2><p className="mt-2 text-sm text-muted-foreground">Attach a PDF, PNG, or JPEG, then choose Review selected credential. Extracted claims are not issuer verification.</p></section>
        <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Evidence contract</h2><p className="mt-2 text-sm text-muted-foreground">AQAA reports UNABLE TO DETERMINE when evidence or sufficient stated facts are absent.</p></section>
        <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Your private workspace</h2><p className="mt-2 text-sm text-muted-foreground">Files, conversations, and saved outputs are scoped to your account.</p></section>
      </div>
      <Link href="/workspace" className="inline-flex min-h-10 items-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Return to workspace</Link>
    </div>
  );
}