import type { Metadata } from "next";
import { InstitutionsList } from "./InstitutionsList";

export const metadata: Metadata = { title: "Institutions" };

export default function InstitutionsPage() {
  return <InstitutionsList />;
}
