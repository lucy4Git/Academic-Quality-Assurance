import type { Metadata } from "next";
import { DashboardView } from "./DashboardView";

export const metadata: Metadata = { title: "Home — AQAA" };

export default function DashboardPage() {
  return <DashboardView />;
}
