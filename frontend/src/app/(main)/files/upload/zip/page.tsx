import type { Metadata } from "next";
import { ZipUploadPageView } from "./ZipUploadPageView";

export const metadata: Metadata = { title: "Bulk ZIP Import" };

export default function ZipUploadPage() {
  return <ZipUploadPageView />;
}
