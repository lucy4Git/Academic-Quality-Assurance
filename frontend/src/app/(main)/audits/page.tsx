import type { Metadata } from "next";
import { AuditCentre } from "./AuditCentre";

export const metadata: Metadata = { title: "Audit Centre" };

export default function AuditCentrePage() {
  return <AuditCentre />;
}
