import type { Metadata } from "next";
import { AiAssistantView } from "./AiAssistantView";

export const metadata: Metadata = {
  title: "AI QA Assistant | AQAA",
  description: "Source-grounded AI assistant for Academic Quality Assurance",
};

export default function AiAssistantPage() {
  return <AiAssistantView />;
}
