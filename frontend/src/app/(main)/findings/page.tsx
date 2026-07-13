import type { Metadata } from "next";
import { FindingsCentre } from "./FindingsCentre";

export const metadata: Metadata = { title: "Findings — AQAA" };

export default function Page() {
  return <FindingsCentre />;
}
