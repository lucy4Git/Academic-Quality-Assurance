import type { Metadata } from "next";
import { CreateFacultyView } from "./CreateFacultyView";

export const metadata: Metadata = { title: "New Faculty" };

export default function CreateFacultyPage() {
  return <CreateFacultyView />;
}
