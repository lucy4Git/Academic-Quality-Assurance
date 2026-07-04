import { AppShell } from "@/components/layout/AppShell";
import { PageRoleGuard } from "@/components/auth/PageRoleGuard";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      <PageRoleGuard>{children}</PageRoleGuard>
    </AppShell>
  );
}
