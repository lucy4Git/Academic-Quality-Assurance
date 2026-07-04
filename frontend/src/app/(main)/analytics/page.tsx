import type { Metadata } from "next";
import { AnalyticsView } from "./AnalyticsView";

export const metadata: Metadata = {
  title: "Analytics | AQAA",
  description: "Institutional QA analytics dashboard",
};

export default function AnalyticsPage() {
  return <AnalyticsView />;
}
