import type { Metadata } from "next";
import { RegulatoryReadiness } from "./RegulatoryReadiness";

export const metadata: Metadata = { title: "Regulatory Readiness — AQAA" };

export default function Page() {
  return <RegulatoryReadiness />;
}
