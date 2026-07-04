import type { Metadata } from "next";
import { QualificationIntelligenceView } from "./QualificationIntelligenceView";

export const metadata: Metadata = {
  title: "Qualification Intelligence | AQAA",
  description: "Advisory GPA/CGPA calculator and NQF qualification mapping tool",
};

export default function QualificationIntelligencePage() {
  return <QualificationIntelligenceView />;
}
