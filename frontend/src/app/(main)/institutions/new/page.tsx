import type { Metadata } from "next";
import { CreateInstitutionView } from "./CreateInstitutionView";

export const metadata: Metadata = { title: "New Institution" };

export default function CreateInstitutionPage() {
  return <CreateInstitutionView />;
}
