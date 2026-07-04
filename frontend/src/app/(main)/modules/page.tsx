import type { Metadata } from "next";
import { ModulesList } from "./ModulesList";

export const metadata: Metadata = { title: "Modules" };

export default function ModulesPage() {
  return <ModulesList />;
}
