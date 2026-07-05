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
import { useUIStore } from "@/store/ui.store";
import { useAuthStore } from "@/store/auth.store";
import { NAV_SECTIONS } from "@/lib/rbac";
import type { UserRole } from "@/types";

const QUICK_ACTIONS = [
  { label: "Upload Evidence ZIP", href: "/files/upload" },
  { label: "Ask AI QA Assistant", href: "/ai-assistant" },
  { label: "Search Knowledge Base", href: "/knowledge-search" },
  { label: "Open Qualification Intelligence", href: "/qualification-intelligence" },
  { label: "View File Library", href: "/files" },
  { label: "Open AI Workspace", href: "/ai-workspace" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const role = user?.role as UserRole | undefined;

  const navItems = NAV_SECTIONS.flatMap((section) =>
    section.items.filter((item) => !role || item.roles.includes(role))
  );

  const runCommand = (href: string) => {
    setCommandPaletteOpen(false);
    router.push(href);
  };

  return (
    <CommandDialog
      open={commandPaletteOpen}
      onOpenChange={setCommandPaletteOpen}
      title="Command Palette"
      description="Search pages and actions"
    >
      <CommandInput placeholder="Search pages and actions…" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          {navItems.map((item) => (
            <CommandItem
              key={item.href}
              value={item.label}
              onSelect={() => runCommand(item.href)}
            >
              {item.label}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Quick Actions">
          {QUICK_ACTIONS.map((action) => (
            <CommandItem
              key={action.href}
              value={action.label}
              onSelect={() => runCommand(action.href)}
            >
              {action.label}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
