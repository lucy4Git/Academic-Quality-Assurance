import type { Metadata } from "next";
import { IkpManagementView } from "./IkpManagementView";

export const metadata: Metadata = {
  title: "IKP Management | AQAA",
  description: "Manage Institutional Knowledge Packages — view chunks, check Qdrant indexing status, trigger re-indexing, and create Knowledge Review batches.",
};

export default function IkpManagementPage() {
  return <IkpManagementView />;
}
