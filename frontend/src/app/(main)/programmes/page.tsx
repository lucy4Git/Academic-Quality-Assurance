import type { Metadata } from "next";
import { ProgrammesList } from "./ProgrammesList";

export const metadata: Metadata = { title: "Programmes" };

export default function ProgrammesPage() {
  return <ProgrammesList />;
}
