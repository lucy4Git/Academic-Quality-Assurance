import type { Metadata } from "next";
import { KnowledgeReviewList } from "./KnowledgeReviewList";

export const metadata: Metadata = { title: "Knowledge Review Centre" };

export default function KnowledgeReviewPage() {
  return <KnowledgeReviewList />;
}
