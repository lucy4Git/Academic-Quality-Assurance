import type { Metadata } from "next";
import { UsersView } from "./UsersView";

export const metadata: Metadata = { title: "User Management" };

export default function UsersPage() {
  return <UsersView />;
}
