import type { Metadata } from "next";
import { FacultiesList } from "./FacultiesList";

export const metadata: Metadata = { title: "Faculties" };

export default function FacultiesPage() {
  return <FacultiesList />;
}
