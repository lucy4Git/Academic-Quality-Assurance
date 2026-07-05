"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  GraduationCap, FileBarChart2, Upload, ShieldCheck, SearchCheck, Brain,
} from "lucide-react";
import { useRole } from "@/hooks/useRole";

interface Suggestion {
  label: string;
  icon: React.ElementType;
  href: string;
  roles: string[];
}

const SUGGESTIONS: Suggestion[] = [
  { label: "Review Engineering Faculty",     icon: GraduationCap, href: "/faculties",                  roles: ["dean", "qa", "admin"] },
  { label: "Generate Senate Report",         icon: FileBarChart2, href: "/reports",                    roles: ["qa", "admin"] },
  { label: "Analyse New Uploads",            icon: Upload,        href: "/files",                       roles: ["all"] },
  { label: "Run Accreditation Review",       icon: ShieldCheck,   href: "/accreditation",               roles: ["dean", "qa", "admin"] },
  { label: "Search Knowledge Base",          icon: SearchCheck,   href: "/knowledge-search",             roles: ["all"] },
  { label: "Open AI Workspace",             icon: Brain,         href: "/ai-workspace",                 roles: ["all"] },
];

export function AISuggestions() {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer, isDean } = useRole();

  const visible = SUGGESTIONS.filter((s) => {
    if (s.roles.includes("all")) return true;
    if (s.roles.includes("admin") && isSysAdmin) return true;
    if (s.roles.includes("qa") && isQAOfficer) return true;
    if (s.roles.includes("dean") && isDean) return true;
    return false;
  });

  return (
    <section>
      <div className="flex items-center gap-2 mb-3">
        <Brain className="h-4 w-4 text-indigo-500" />
        <h2 className="text-base font-semibold text-foreground">AI Suggestions</h2>
      </div>
      <div className="flex flex-wrap gap-2">
        {visible.map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.button
              key={s.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25, delay: i * 0.05 }}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => router.push(s.href)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-full border border-border bg-card text-sm text-foreground hover:border-indigo-400 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/30 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors font-medium"
            >
              <Icon className="h-3.5 w-3.5 flex-shrink-0" />
              {s.label}
            </motion.button>
          );
        })}
      </div>
    </section>
  );
}
