import type { Metadata } from "next";
import { DepartmentsList } from "./DepartmentsList";

export const metadata: Metadata = { title: "Departments" };

export default function DepartmentsPage() {
  return <DepartmentsList />;
}
