import type { Metadata } from "next";
import { ItemReviewDetail } from "./ItemReviewDetail";

export const metadata: Metadata = { title: "Review Item" };

interface PageProps {
  params: Promise<{ itemId: string }>;
}

export default async function ItemReviewPage({ params }: PageProps) {
  const { itemId } = await params;
  return <ItemReviewDetail itemId={itemId} />;
}
