import type { Metadata } from "next";
import { FrameworkManagement } from "./FrameworkManagement";

export const metadata: Metadata = { title: "Framework Management — AQAA" };

export default function Page() {
  return <FrameworkManagement />;
}
