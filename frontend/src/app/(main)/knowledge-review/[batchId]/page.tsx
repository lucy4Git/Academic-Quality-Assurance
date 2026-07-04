import type { Metadata } from "next";
import { BatchReviewDetail } from "./BatchReviewDetail";

export const metadata: Metadata = { title: "Review Batch" };

interface PageProps {
  params: Promise<{ batchId: string }>;
}

export default async function BatchReviewPage({ params }: PageProps) {
  const { batchId } = await params;
  return <BatchReviewDetail batchId={batchId} />;
}
