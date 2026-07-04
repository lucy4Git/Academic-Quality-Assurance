import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/common/PlaceholderPage";

export const metadata: Metadata = { title: "Profile" };

export default function Page() {
  return <PlaceholderPage title="My Profile" />;
}