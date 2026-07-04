"use client";

import { useState, useCallback } from "react";
import { useCalculate, useSaveRecord, useQualificationRecords, useDeleteQualificationRecord } from "@/hooks/useQualification";
import type { SubjectEntry, CalculationResult } from "@/types/qualification";

const QUAL_TYPES = [
  { value: "certificate", label: "Higher Certificate (NQF 5)" },
  { value: "diploma", label: "Diploma (NQF 6)" },
  { value: "bachelor", label: "Bachelor's Degree (NQF 7)" },
  { value: "honours", label: "Honours / Postgrad Diploma (NQF 8)" },
  { value: "masters", label: "Master's Degree (NQF 9)" },
  { value: "doctoral", label: "Doctoral Degree (NQF 10)" },
];

const EMPTY_ENTRY: SubjectEntry = { name: "", credits: 16, percentage: 0, semester: 1 };

function DisclaimerBanner() {
  return (
    <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <strong>Advisory only.</strong> This tool does NOT produce official SAQA evaluations or formal
      academic credential assessments. Results are for internal advisory purposes only. Contact SAQA
      or the relevant Quality Council for official evaluations.
    </div>
  );
}

function GradeLabel({ grade, passed }: { grade: string; passed: boolean }) {
  const colour = passed
    ? "bg-green-100 text-green-700"
    : "bg-red-100 text-red-600";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colour}`}>
      {grade}
    </span>
  );
}

function GPABadge({ gpa }: { gpa: number }) {
  const colour =
    gpa >= 3.7 ? "bg-green-100 text-green-700" :
    gpa >= 3.0 ? "bg-blue-100 text-blue-700" :
    gpa >= 2.0 ? "bg-yellow-100 text-yellow-700" :
    "bg-red-100 text-red-600";
  return (
    <span className={`rounded-lg px-3 py-1 text-sm font-bold ${colour}`}>
      {gpa.toFixed(2)} / 4.00
    </span>
  );
}

interface EntryRowProps {
  entry: SubjectEntry;
  index: number;
  onChange: (i: number, field: keyof SubjectEntry, value: string | number) => void;
  onRemove: (i: number) => void;
}

function EntryRow({ entry, index, onChange, onRemove }: EntryRowProps) {
  return (
    <div className="grid grid-cols-12 gap-2 items-center">
      <input
        className="col-span-4 rounded border border-gray-300 px-2 py-1.5 text-sm"
        placeholder="Subject name"
        value={entry.name}
        onChange={(e) => onChange(index, "name", e.target.value)}
      />
      <input
        type="number"
        className="col-span-2 rounded border border-gray-300 px-2 py-1.5 text-sm"
        placeholder="Credits"
        min={1}
        max={240}
        value={entry.credits}
        onChange={(e) => onChange(index, "credits", parseFloat(e.target.value) || 0)}
      />
      <input
        type="number"
        className="col-span-2 rounded border border-gray-300 px-2 py-1.5 text-sm"
        placeholder="%"
        min={0}
        max={100}
        value={entry.percentage}
        onChange={(e) => onChange(index, "percentage", parseFloat(e.target.value) || 0)}
      />
      <input
        type="number"
        className="col-span-2 rounded border border-gray-300 px-2 py-1.5 text-sm"
        placeholder="Sem"
        min={1}
        max={12}
        value={entry.semester}
        onChange={(e) => onChange(index, "semester", parseInt(e.target.value) || 1)}
      />
      <button
        onClick={() => onRemove(index)}
        className="col-span-2 text-red-500 hover:text-red-700 text-sm font-medium"
      >
        Remove
      </button>
    </div>
  );
}

function ResultPanel({ result }: { result: CalculationResult }) {
  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-xs text-gray-500 mb-1">GPA</p>
          <GPABadge gpa={result.gpa} />
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-xs text-gray-500 mb-1">CGPA</p>
          <GPABadge gpa={result.cgpa} />
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-xs text-gray-500 mb-1">Total Credits</p>
          <p className="text-lg font-bold text-gray-900">{result.total_credits.toFixed(0)}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-xs text-gray-500 mb-1">Pass Rate</p>
          <p className="text-lg font-bold text-gray-900">{result.pass_rate.toFixed(0)}%</p>
          <p className="text-xs text-gray-400">{result.passed_subjects}/{result.subjects.length} subjects</p>
        </div>
      </div>

      {/* NQF advisory */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-blue-600 mb-1">Advisory NQF Mapping</p>
        <p className="font-bold text-blue-900 text-lg">
          NQF Level {result.nqf_advisory.advisory_level} — {result.nqf_advisory.advisory_label}
        </p>
        <p className="text-sm text-blue-700 mt-1">{result.nqf_advisory.advisory_note}</p>
      </div>

      {/* Advisory summary */}
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Advisory Summary</p>
        <p className="text-sm text-gray-700 leading-relaxed">{result.advisory_summary}</p>
      </div>

      {/* Warnings */}
      {result.advisory_warnings.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-red-600 mb-2">Warnings</p>
          <ul className="space-y-1">
            {result.advisory_warnings.map((w, i) => (
              <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                <span className="mt-0.5 shrink-0">⚠</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      <div className="rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-green-600 mb-2">Recommendations</p>
        <ul className="space-y-1">
          {result.advisory_recommendations.map((r, i) => (
            <li key={i} className="text-sm text-green-800 flex items-start gap-2">
              <span className="mt-0.5 shrink-0">→</span>
              {r}
            </li>
          ))}
        </ul>
      </div>

      {/* Semester breakdown */}
      {result.semesters.length > 1 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Semester GPA Breakdown</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {result.semesters.map((s) => (
              <div key={s.semester} className="text-center p-3 rounded-lg bg-gray-50">
                <p className="text-xs text-gray-500">Semester {s.semester}</p>
                <p className="font-bold text-gray-900">{s.gpa.toFixed(2)}</p>
                <p className="text-xs text-gray-400">{s.credits} cr · {s.subjects} subj</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Subject table */}
      <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
        <p className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500 border-b border-gray-100">
          Subject Breakdown
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-500 text-xs">
                <th className="text-left px-4 py-2">Subject</th>
                <th className="text-right px-3 py-2">Credits</th>
                <th className="text-right px-3 py-2">%</th>
                <th className="text-center px-3 py-2">Grade</th>
                <th className="text-right px-3 py-2">GPA pts</th>
                <th className="text-right px-3 py-2">Quality pts</th>
                <th className="text-center px-3 py-2">Sem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {result.subjects.map((s, i) => (
                <tr key={i} className={s.passed ? "" : "bg-red-50/40"}>
                  <td className="px-4 py-2 font-medium text-gray-900">{s.name}</td>
                  <td className="px-3 py-2 text-right text-gray-600">{s.credits}</td>
                  <td className="px-3 py-2 text-right text-gray-600">{s.percentage}%</td>
                  <td className="px-3 py-2 text-center">
                    <GradeLabel grade={s.letter_grade} passed={s.passed} />
                  </td>
                  <td className="px-3 py-2 text-right text-gray-600">{s.grade_points.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right text-gray-600">{s.quality_points.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center text-gray-500">{s.semester}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-gray-400 italic leading-relaxed">{result.disclaimer}</p>
    </div>
  );
}

export function QualificationIntelligenceView() {
  const [studentName, setStudentName] = useState("");
  const [institutionName, setInstitutionName] = useState("");
  const [programmeName, setProgrammeName] = useState("");
  const [qualType, setQualType] = useState("bachelor");
  const [academicYear, setAcademicYear] = useState("");
  const [notes, setNotes] = useState("");
  const [entries, setEntries] = useState<SubjectEntry[]>([{ ...EMPTY_ENTRY }]);
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [activeTab, setActiveTab] = useState<"calculator" | "history">("calculator");

  const calculate = useCalculate();
  const saveRecord = useSaveRecord();
  const { data: records } = useQualificationRecords();
  const deleteRecord = useDeleteQualificationRecord();

  const handleEntryChange = useCallback(
    (i: number, field: keyof SubjectEntry, value: string | number) => {
      setEntries((prev) => {
        const next = [...prev];
        next[i] = { ...next[i], [field]: value };
        return next;
      });
    },
    []
  );

  const handleRemove = useCallback((i: number) => {
    setEntries((prev) => prev.filter((_, idx) => idx !== i));
  }, []);

  const handleAddRow = useCallback(() => {
    setEntries((prev) => [...prev, { ...EMPTY_ENTRY }]);
  }, []);

  const handleCalculate = useCallback(async () => {
    const validEntries = entries.filter((e) => e.name.trim());
    if (validEntries.length === 0) return;
    const res = await calculate.mutateAsync({
      student_name: studentName,
      institution_name: institutionName,
      programme_name: programmeName,
      qualification_type: qualType,
      academic_year: academicYear || null,
      entries: validEntries,
      notes: notes || null,
    });
    setResult(res);
  }, [entries, studentName, institutionName, programmeName, qualType, academicYear, notes, calculate]);

  const handleSave = useCallback(async () => {
    if (!result) return;
    const validEntries = entries.filter((e) => e.name.trim());
    await saveRecord.mutateAsync({
      student_name: studentName,
      institution_name: institutionName,
      programme_name: programmeName,
      qualification_type: qualType,
      academic_year: academicYear || null,
      entries: validEntries,
      notes: notes || null,
    });
  }, [result, entries, studentName, institutionName, programmeName, qualType, academicYear, notes, saveRecord]);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Qualification Intelligence</h1>
        <p className="text-sm text-gray-500 mt-1">
          Advisory GPA/CGPA calculator and NQF qualification mapping tool.
        </p>
      </div>

      <DisclaimerBanner />

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {(["calculator", "history"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
              activeTab === tab
                ? "border-b-2 border-blue-600 text-blue-700"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab === "calculator" ? "Calculator" : `Saved Records${records ? ` (${records.length})` : ""}`}
          </button>
        ))}
      </div>

      {activeTab === "calculator" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Input form */}
          <div className="space-y-5">
            <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-4">
              <p className="text-sm font-semibold text-gray-700">Student & Programme Details</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Student name</label>
                  <input
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    placeholder="e.g. Jane Dlamini"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Institution</label>
                  <input
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                    value={institutionName}
                    onChange={(e) => setInstitutionName(e.target.value)}
                    placeholder="e.g. TUT"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Programme name</label>
                  <input
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                    value={programmeName}
                    onChange={(e) => setProgrammeName(e.target.value)}
                    placeholder="e.g. BSc Computer Science"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Qualification type</label>
                  <select
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                    value={qualType}
                    onChange={(e) => setQualType(e.target.value)}
                  >
                    {QUAL_TYPES.map((q) => (
                      <option key={q.value} value={q.value}>{q.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Academic year</label>
                  <input
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                    placeholder="e.g. 2024"
                  />
                </div>
              </div>
            </div>

            {/* Subject entries */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-3">
              <p className="text-sm font-semibold text-gray-700">Subject / Module Entries</p>
              <div className="grid grid-cols-12 gap-2 text-xs text-gray-500 font-medium px-0">
                <span className="col-span-4">Subject</span>
                <span className="col-span-2">Credits</span>
                <span className="col-span-2">Mark %</span>
                <span className="col-span-2">Semester</span>
                <span className="col-span-2"></span>
              </div>
              <div className="space-y-2">
                {entries.map((entry, i) => (
                  <EntryRow
                    key={i}
                    entry={entry}
                    index={i}
                    onChange={handleEntryChange}
                    onRemove={handleRemove}
                  />
                ))}
              </div>
              <button
                onClick={handleAddRow}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                + Add subject
              </button>
            </div>

            {/* Notes */}
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <label className="block text-xs text-gray-500 mb-1">Notes (optional)</label>
              <textarea
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm resize-none"
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any additional context..."
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={handleCalculate}
                disabled={calculate.isPending || entries.filter((e) => e.name.trim()).length === 0}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {calculate.isPending ? "Calculating…" : "Calculate"}
              </button>
              {result && (
                <button
                  onClick={handleSave}
                  disabled={saveRecord.isPending}
                  className="rounded-lg border border-blue-300 px-4 py-3 text-sm font-medium text-blue-700 hover:bg-blue-50 disabled:opacity-50 transition-colors"
                >
                  {saveRecord.isPending ? "Saving…" : "Save Record"}
                </button>
              )}
            </div>

            {saveRecord.isSuccess && (
              <p className="text-sm text-green-600 font-medium">Record saved successfully.</p>
            )}
          </div>

          {/* Right: Results */}
          <div>
            {result ? (
              <ResultPanel result={result} />
            ) : (
              <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 flex flex-col items-center justify-center py-20 text-center">
                <p className="text-gray-400 text-sm">Enter subject marks and click Calculate</p>
                <p className="text-gray-300 text-xs mt-1">Results will appear here</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "history" && (
        <div>
          {!records || records.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 flex flex-col items-center justify-center py-16 text-center">
              <p className="text-gray-400 text-sm">No saved records yet.</p>
              <p className="text-gray-300 text-xs mt-1">Calculate and save a record to see it here.</p>
            </div>
          ) : (
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-500 text-xs border-b border-gray-200">
                    <th className="text-left px-4 py-3">Student</th>
                    <th className="text-left px-4 py-3">Programme</th>
                    <th className="text-right px-4 py-3">GPA</th>
                    <th className="text-right px-4 py-3">Credits</th>
                    <th className="text-left px-4 py-3">Advisory NQF</th>
                    <th className="text-left px-4 py-3">Date</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {records.map((r) => (
                    <tr key={r.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{r.student_name || "—"}</td>
                      <td className="px-4 py-3 text-gray-600">{r.programme_name || "—"}</td>
                      <td className="px-4 py-3 text-right">
                        <GPABadge gpa={r.gpa} />
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">{r.total_credits.toFixed(0)}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {r.nqf_advisory_level ? `Level ${r.nqf_advisory_level} — ${r.nqf_advisory_label}` : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {new Date(r.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => deleteRecord.mutate(r.id)}
                          className="text-red-500 hover:text-red-700 text-xs"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
