import type { Metadata } from "next";
import { ReportsView } from "./ReportsView";

export const metadata: Metadata = {
  title: "Reports | AQAA",
  description: "Export institutional QA reports",
};

export default function ReportsPage() {
  return <ReportsView />;
}
