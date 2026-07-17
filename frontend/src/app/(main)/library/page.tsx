import type { Metadata } from "next";
import { LibraryView } from "./LibraryView";

export const metadata: Metadata = { title: "Library — AQAA" };

export default function LibraryPage() {
  return <LibraryView />;
}
