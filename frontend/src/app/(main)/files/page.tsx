import type { Metadata } from "next";
import { FileLibrary } from "./FileLibrary";

export const metadata: Metadata = { title: "File Library" };

export default function FileLibraryPage() {
  return <FileLibrary />;
}
