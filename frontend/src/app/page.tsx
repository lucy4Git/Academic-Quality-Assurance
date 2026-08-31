import Link from "next/link";
import { ArrowRight, CheckCircle2, FileCheck2, Paperclip, ShieldCheck, Sparkles } from "lucide-react";

const capabilities = [
  ["Evidence-aware review", "Attach module, assessment, or moderation evidence and receive findings tied to the files AQAA actually inspected."],
  ["Clear quality findings", "Distinguish present, missing, incomplete, and unable-to-determine states without inventing evidence."],
  ["Actionable remediation", "Turn each gap into a prioritised next step you can prepare, review, and save."],
];

export default function HomePage() {
  return (
    <div className="min-h-screen overflow-hidden bg-[#f8f8f6] text-[#171815]">
      <nav className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
        <Link href="/" className="flex items-center gap-3" aria-label="AQAA home">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#1d3d35] text-xs font-bold text-white">AQ</span>
          <span className="font-semibold tracking-tight">AQAA</span>
        </Link>
        <div className="flex items-center gap-2">
          <Link href="/login" className="rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-black/5">Sign in</Link>
          <Link href="/register" className="rounded-xl bg-[#1d3d35] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#153029]">Start with AQAA</Link>
        </div>
      </nav>

      <main>
        <section className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 pb-24 pt-16 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:pb-32 lg:pt-24">
          <div className="relative z-10">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#1d3d35]/15 bg-white/70 px-3 py-1.5 text-xs font-semibold text-[#1d3d35] shadow-sm backdrop-blur">
              <Sparkles className="h-3.5 w-3.5" /> Academic quality assurance AI
            </div>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[1.02] tracking-[-0.045em] sm:text-6xl lg:text-7xl">
              Review evidence.<br />Find quality gaps.<br /><span className="text-[#527068]">Prepare confidently.</span>
            </h1>
            <p className="mt-7 max-w-xl text-lg leading-8 text-[#5f635e]">
              AQAA is one intelligent workspace for reviewing module and course evidence, assessment readiness, moderation, learning outcomes, and quality findings.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link href="/register" className="inline-flex h-12 items-center justify-center rounded-xl bg-[#1d3d35] px-6 text-sm font-semibold text-white shadow-[0_12px_30px_-15px_#1d3d35] transition hover:-translate-y-0.5 hover:bg-[#153029] motion-reduce:transform-none">Start with AQAA <ArrowRight className="ml-2 h-4 w-4" /></Link>
              <Link href="/login" className="inline-flex h-12 items-center justify-center rounded-xl border border-black/10 bg-white px-6 text-sm font-semibold shadow-sm transition hover:bg-black/[0.025]">Sign in</Link>
            </div>
            <p className="mt-5 text-xs text-[#777b75]">For individual academic quality work. <Link href="/login" className="font-medium underline underline-offset-4">For institutions</Link></p>
          </div>

          <div className="relative">
            <div className="absolute -inset-16 -z-10 rounded-full bg-[#dbe7df]/70 blur-3xl" />
            <div className="overflow-hidden rounded-[2rem] border border-black/10 bg-white shadow-[0_35px_100px_-45px_rgba(20,50,42,.45)]">
              <div className="flex items-center justify-between border-b border-black/[0.07] px-5 py-4">
                <div className="flex items-center gap-2.5"><span className="grid h-7 w-7 place-items-center rounded-lg bg-[#1d3d35] text-[9px] font-bold text-white">AQ</span><span className="text-sm font-semibold">Module evidence review</span></div>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#eef5f0] px-2.5 py-1 text-[11px] font-medium text-[#31594d]"><span className="h-1.5 w-1.5 rounded-full bg-[#4b806f]" />Evidence grounded</span>
              </div>
              <div className="space-y-5 bg-[#fcfcfa] p-5 sm:p-7">
                <div className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-[#1d3d35] px-4 py-3 text-sm leading-6 text-white">Review the attached evidence and identify the most important quality gaps.</div>
                <div className="flex gap-2 overflow-hidden">
                  <span className="inline-flex min-w-0 items-center gap-2 rounded-xl border bg-white px-3 py-2 text-xs text-[#555a55] shadow-sm"><FileCheck2 className="h-4 w-4 shrink-0 text-[#477062]" /><span className="truncate">Assessment_Pack.pdf</span><CheckCircle2 className="h-3.5 w-3.5 text-[#4b806f]" /></span>
                </div>
                <div className="rounded-2xl rounded-tl-md border border-black/[0.08] bg-white p-5 shadow-sm">
                  <div className="mb-4 flex items-center justify-between gap-3"><p className="text-sm font-semibold">Priority quality finding</p><span className="rounded-full bg-[#fff3db] px-2.5 py-1 text-[10px] font-bold tracking-wide text-[#805c19]">INCOMPLETE</span></div>
                  <dl className="space-y-3 text-sm">
                    <div><dt className="text-xs font-semibold uppercase tracking-wider text-[#8a8e88]">Evidence</dt><dd className="mt-1 leading-6">Assessment paper and rubric are present; no approved memorandum is visible.</dd></div>
                    <div><dt className="text-xs font-semibold uppercase tracking-wider text-[#8a8e88]">Why it matters</dt><dd className="mt-1 leading-6">Moderation cannot verify marking consistency without expected answers or guidance.</dd></div>
                    <div className="rounded-xl bg-[#eef5f0] p-3"><dt className="text-xs font-semibold uppercase tracking-wider text-[#31594d]">Recommended remediation</dt><dd className="mt-1 leading-6">Prepare the memorandum, align it to the rubric, then record moderation approval.</dd></div>
                  </dl>
                  <button className="mt-4 inline-flex items-center gap-2 text-xs font-medium text-[#31594d]"><Paperclip className="h-3.5 w-3.5" />Assessment_Pack.pdf · page 6</button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-black/[0.07] bg-white">
          <div className="mx-auto grid max-w-7xl gap-px bg-black/[0.07] md:grid-cols-3">
            {capabilities.map(([title, description], index) => (
              <article key={title} className="bg-white px-7 py-10 sm:px-10">
                <span className="mb-6 grid h-10 w-10 place-items-center rounded-xl bg-[#eef5f0] text-[#31594d]">{index === 0 ? <Paperclip className="h-5 w-5" /> : index === 1 ? <ShieldCheck className="h-5 w-5" /> : <CheckCircle2 className="h-5 w-5" />}</span>
                <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
                <p className="mt-3 text-sm leading-6 text-[#686c67]">{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-4xl px-5 py-24 text-center sm:px-8 sm:py-32">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#527068]">One workspace. Evidence first.</p>
          <h2 className="mt-4 text-4xl font-semibold tracking-[-0.035em] sm:text-5xl">Academic quality work without the portal maze.</h2>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-[#686c67]">Ask one question. AQAA selects the relevant quality capability, preserves context, checks your evidence, and returns one clear response in the same conversation.</p>
          <Link href="/register" className="mt-8 inline-flex h-12 items-center rounded-xl bg-[#1d3d35] px-6 text-sm font-semibold text-white">Start with AQAA <ArrowRight className="ml-2 h-4 w-4" /></Link>
        </section>
      </main>

      <footer className="border-t border-black/[0.07] px-5 py-8 text-sm text-[#747872] sm:px-8"><div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 sm:flex-row"><span>AQAA · Academic Quality Assurance AI</span><span>Evidence. Judgement. Assurance.</span></div></footer>
    </div>
  );
}
