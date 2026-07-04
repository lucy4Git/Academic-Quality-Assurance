import Link from "next/link";

const FEATURES = [
  {
    icon: "🔍",
    title: "AI QA Workspace",
    desc: "Ask any quality assurance question in plain language. AQAA routes to the right agent automatically — assessment, moderation, accreditation, evidence, and more.",
  },
  {
    icon: "🤖",
    title: "Multi-Agent Orchestration",
    desc: "Complex queries engage multiple specialised agents simultaneously. Get a comprehensive answer from Evidence, Accreditation, and Reporting agents in one request.",
  },
  {
    icon: "📚",
    title: "Institutional Knowledge Portal",
    desc: "Vector-indexed institutional knowledge base. Search across programmes, modules, policies, and regulations with semantic understanding.",
  },
  {
    icon: "📋",
    title: "ADIP Audit Agents",
    desc: "Eight AI audit agents covering the full Academic Development and Improvement Programme checklist: assessment, moderation, attendance, evidence, outcomes, accreditation, programme review.",
  },
  {
    icon: "📦",
    title: "Bulk ZIP Document Import",
    desc: "Upload a ZIP of module documents. AQAA classifies each file by type, identifies missing required categories, and queues them for scanning.",
  },
  {
    icon: "🎓",
    title: "Qualification Intelligence",
    desc: "Calculate GPA, CGPA, and NQF advisory outcomes. South African higher education standards built in.",
  },
  {
    icon: "📊",
    title: "Reports & Analytics",
    desc: "Export compliance summaries as CSV, Excel, or PDF. Dashboard analytics across all audits, evidence, and knowledge activity.",
  },
  {
    icon: "🔐",
    title: "Tenant Isolation",
    desc: "Multi-institutional architecture with strict tenant isolation. Every query, every document, every audit is scoped to its institution.",
  },
];

const AGENTS = [
  { name: "Assessment Compliance", icon: "📝", desc: "Audit assessment plans, marks, and rubrics." },
  { name: "Moderation Compliance", icon: "🔄", desc: "Internal and external moderation records." },
  { name: "Attendance Compliance", icon: "📅", desc: "Register completeness and attendance thresholds." },
  { name: "Evidence Verification", icon: "📁", desc: "Module folder evidence completeness." },
  { name: "Outcome Alignment", icon: "🎯", desc: "Graduate attribute and curriculum alignment." },
  { name: "Accreditation Readiness", icon: "🏛️", desc: "HEQSF, ECSA, HPCSA, CHE readiness." },
  { name: "Programme Review", icon: "🔎", desc: "Periodic programme quality evaluation." },
  { name: "Qualification Intelligence", icon: "🎓", desc: "GPA, CGPA, and NQF advisory calculations." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Nav */}
      <nav className="border-b border-gray-100 px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
            <span className="text-xs font-bold text-white">AQ</span>
          </div>
          <span className="font-bold text-gray-900">AQAA</span>
          <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-700 ml-1">
            RC4
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
          >
            Request access
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-xs font-medium text-indigo-700 mb-6">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
          TUT and UP pilot institutions active
        </div>
        <h1 className="text-5xl font-extrabold text-gray-900 leading-tight mb-6">
          Academic Quality Assurance,{" "}
          <span className="text-indigo-600">powered by AI</span>
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed mb-10">
          AQAA is an enterprise AI platform for South African higher education institutions.
          Automate ADIP audits, verify evidence, ensure accreditation readiness, and answer
          any QA question in plain language — all within your institution&apos;s secure workspace.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/register"
            className="rounded-xl bg-indigo-600 px-8 py-3.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200"
          >
            Request pilot access
          </Link>
          <Link
            href="/login"
            className="rounded-xl border border-gray-200 px-8 py-3.5 text-sm font-semibold text-gray-700 hover:border-indigo-300 hover:bg-gray-50 transition-colors"
          >
            Sign in to your workspace
          </Link>
        </div>
      </section>

      {/* Pilot institutions */}
      <section className="border-y border-gray-100 bg-gray-50 py-10">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-6">
            Active pilot institutions
          </p>
          <div className="flex flex-wrap justify-center gap-8">
            {[
              { code: "TUT", name: "Tshwane University of Technology", scope: "ICT Faculty · 22 programmes · 174 modules" },
              { code: "UP", name: "University of Pretoria", scope: "EBIT Faculty · CS, INF, IS · 10 programmes" },
            ].map((inst) => (
              <div key={inst.code} className="flex flex-col items-center gap-1">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-gray-200 shadow-sm">
                  <span className="text-xs font-bold text-indigo-600">{inst.code}</span>
                </div>
                <p className="text-sm font-semibold text-gray-800">{inst.name}</p>
                <p className="text-xs text-gray-400">{inst.scope}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features grid */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">Everything your QA team needs</h2>
          <p className="text-gray-500">
            One platform for audits, evidence, knowledge, reporting, and AI-assisted quality assurance.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-gray-100 bg-gray-50 p-5 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all"
            >
              <span className="text-2xl mb-3 block">{f.icon}</span>
              <h3 className="text-sm font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Agent showcase */}
      <section className="bg-indigo-600 py-20">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">8 Specialised AI Audit Agents</h2>
            <p className="text-indigo-200">
              Each agent is trained on the full ADIP framework and institutional QA requirements.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {AGENTS.map((a) => (
              <div
                key={a.name}
                className="rounded-xl border border-indigo-500 bg-indigo-700/50 p-4 text-center hover:bg-indigo-700 transition-colors"
              >
                <span className="text-2xl mb-2 block">{a.icon}</span>
                <p className="text-xs font-semibold text-white mb-1">{a.name}</p>
                <p className="text-[11px] text-indigo-200 leading-relaxed">{a.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow section */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">The QA workflow, end-to-end</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-4 items-center">
          {[
            { n: "1", label: "Register", desc: "Request institutional access" },
            { n: "→", label: "" , desc: "" },
            { n: "2", label: "Upload", desc: "Import evidence and documents" },
            { n: "→", label: "", desc: "" },
            { n: "3", label: "Audit", desc: "AI agents run ADIP compliance checks" },
          ].map((step, i) =>
            step.n === "→" ? (
              <div key={i} className="hidden sm:flex justify-center text-gray-300 text-2xl">→</div>
            ) : (
              <div key={i} className="rounded-2xl border border-gray-100 bg-gray-50 p-5 text-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white font-bold text-sm mx-auto mb-3">
                  {step.n}
                </div>
                <p className="text-sm font-semibold text-gray-900">{step.label}</p>
                <p className="text-xs text-gray-400 mt-1">{step.desc}</p>
              </div>
            )
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 max-w-sm mx-auto sm:max-w-none sm:grid-cols-3">
          {[
            { n: "4", label: "Review", desc: "Findings and recommendations" },
            { n: "5", label: "Ask AI", desc: "Natural language Q&A workspace" },
            { n: "6", label: "Report", desc: "Export compliance reports" },
          ].map((step) => (
            <div key={step.n} className="rounded-2xl border border-gray-100 bg-gray-50 p-5 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white font-bold text-sm mx-auto mb-3">
                {step.n}
              </div>
              <p className="text-sm font-semibold text-gray-900">{step.label}</p>
              <p className="text-xs text-gray-400 mt-1">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-gray-100 bg-gray-50 py-20">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to modernise your QA process?
          </h2>
          <p className="text-gray-500 mb-8">
            Join TUT and UP as an AQAA pilot institution. Registration is reviewed by a System
            Administrator — access is granted within 24 hours.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="rounded-xl bg-indigo-600 px-8 py-3.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-100"
            >
              Request access →
            </Link>
            <Link
              href="/login"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Already have an account? Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-indigo-600">
              <span className="text-[9px] font-bold text-white">AQ</span>
            </div>
            <span className="text-xs text-gray-400">
              AQAA — Academic Quality Assurance Agent · v1.0.0-rc4
            </span>
          </div>
          <div className="flex items-center gap-6 text-xs text-gray-400">
            <Link href="/login" className="hover:text-gray-600 transition-colors">Sign in</Link>
            <Link href="/register" className="hover:text-gray-600 transition-colors">Register</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
