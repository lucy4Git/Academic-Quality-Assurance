"use client";

import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from "@/components/ui/command";
import {
  Home,
  LayoutGrid,
  BookOpen,
  ShieldCheck,
  Settings2,
  Brain,
  Upload,
  SearchCheck,
  FileText,
  Users,
  Building2,
  Zap,
  MessageSquare,
  Database,
  Download,
  ClipboardCheck,
  BarChart2,
  type LucideIcon,
} from "lucide-react";
import { useUIStore } from "@/store/ui.store";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

interface CommandEntry {
  label: string;
  href: string;
  icon: LucideIcon;
  roles?: UserRole[];
  group: string;
}

const ALL_ROLES: UserRole[] = [
  "system_admin", "quality_assurance_officer", "faculty_dean",
  "head_of_department", "programme_coordinator", "lecturer", "student",
];
const STAFF: UserRole[] = [
  "system_admin", "quality_assurance_officer", "faculty_dean",
  "head_of_department", "programme_coordinator", "lecturer",
];
const QA: UserRole[] = ["system_admin", "quality_assurance_officer"];
const SA: UserRole[] = ["system_admin"];

const COMMANDS: CommandEntry[] = [
  // Navigation
  { label: "Home",           href: "/dashboard",      icon: Home,         roles: ALL_ROLES, group: "Navigate" },
  { label: "Workspace",      href: "/workspace",      icon: LayoutGrid,   roles: STAFF,     group: "Navigate" },
  { label: "Knowledge",      href: "/knowledge",      icon: BookOpen,     roles: STAFF,     group: "Navigate" },
  { label: "Quality",        href: "/quality",        icon: ShieldCheck,  roles: STAFF,     group: "Navigate" },
  { label: "Administration", href: "/administration", icon: Settings2,    roles: SA,        group: "Navigate" },

  // AI Actions
  { label: "Ask AQAA",                   href: "/ai-assistant",             icon: Brain,    roles: STAFF, group: "AI Actions" },
  { label: "Open AI Workspace",          href: "/ai-workspace",             icon: MessageSquare, roles: STAFF, group: "AI Actions" },
  { label: "Qualification Intelligence", href: "/qualification-intelligence", icon: Zap,   roles: STAFF, group: "AI Actions" },

  // Knowledge
  { label: "Knowledge Foundation",    href: "/knowledge/foundation",   icon: Database,      roles: STAFF, group: "Knowledge" },
  { label: "Public Acquisition",      href: "/knowledge/acquisition",  icon: Download,      roles: QA,    group: "Knowledge" },
  { label: "Extraction Review",       href: "/knowledge/acquisition/extraction", icon: ClipboardCheck, roles: QA, group: "Knowledge" },
  { label: "Knowledge Search",        href: "/knowledge-search",       icon: SearchCheck,   roles: STAFF, group: "Knowledge" },

  // Quality
  { label: "Audit Centre",      href: "/audits",         icon: ShieldCheck, roles: STAFF, group: "Quality" },
  { label: "File Library",      href: "/files",          icon: FileText,    roles: STAFF, group: "Quality" },
  { label: "Upload Evidence",   href: "/files/upload",   icon: Upload,      roles: STAFF, group: "Quality" },
  { label: "Findings",          href: "/findings",       icon: BarChart2,   roles: STAFF, group: "Quality" },

  // Administration
  { label: "Users",           href: "/users",              icon: Users,      roles: SA, group: "Administration" },
  { label: "Institutions",    href: "/institutions",        icon: Building2,  roles: QA, group: "Administration" },
  { label: "AI Providers",    href: "/settings/ai-providers", icon: Zap,    roles: SA, group: "Administration" },
  { label: "System Settings", href: "/settings/system",   icon: Settings2,  roles: SA, group: "Administration" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;

  const visible = COMMANDS.filter(
    (c) => !role || !c.roles || c.roles.includes(role)
  );

  const grouped = visible.reduce<Record<string, CommandEntry[]>>((acc, cmd) => {
    (acc[cmd.group] ??= []).push(cmd);
    return acc;
  }, {});

  const runCommand = (href: string) => {
    setCommandPaletteOpen(false);
    router.push(href);
  };

  return (
    <CommandDialog
      open={commandPaletteOpen}
      onOpenChange={setCommandPaletteOpen}
      title="Command Centre"
      description="Search pages, actions, and AI commands"
    >
      <CommandInput placeholder="Search pages, people, commands…" />
      <CommandList className="max-h-[420px]">
        <CommandEmpty>
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">No results found.</p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Try searching for a page, feature, or action.
            </p>
          </div>
        </CommandEmpty>

        {Object.entries(grouped).map(([group, items], idx) => (
          <div key={group}>
            {idx > 0 && <CommandSeparator />}
            <CommandGroup heading={group}>
              {items.map((item) => {
                const Icon = item.icon;
                return (
                  <CommandItem
                    key={item.href}
                    value={`${group} ${item.label}`}
                    onSelect={() => runCommand(item.href)}
                    className="flex items-center gap-2.5 py-2.5 cursor-pointer"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" aria-hidden="true" />
                    <span>{item.label}</span>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </div>
        ))}
      </CommandList>

      {/* Footer hint */}
      <div className="flex items-center justify-between border-t border-border px-3 py-2">
        <div className="flex items-center gap-3 text-[11px] text-muted-foreground/60">
          <span className="flex items-center gap-1">
            <kbd className="h-4 px-1 rounded border bg-muted text-[10px]">↑↓</kbd>
            Navigate
          </span>
          <span className="flex items-center gap-1">
            <kbd className="h-4 px-1 rounded border bg-muted text-[10px]">↵</kbd>
            Open
          </span>
          <span className="flex items-center gap-1">
            <kbd className="h-4 px-1 rounded border bg-muted text-[10px]">Esc</kbd>
            Close
          </span>
        </div>
        <span className="text-[11px] text-muted-foreground/40">AQAA Command Centre</span>
      </div>
    </CommandDialog>
  );
}
