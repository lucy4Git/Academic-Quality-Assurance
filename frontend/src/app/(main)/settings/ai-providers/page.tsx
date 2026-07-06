import type { Metadata } from "next";
import { AIProvidersView } from "./AIProvidersView";

export const metadata: Metadata = { title: "AI Provider Settings — AQAA" };

export default function Page() {
  return <AIProvidersView />;
}
