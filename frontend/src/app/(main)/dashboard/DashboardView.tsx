"use client";

import { memo } from "react";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { useRole } from "@/hooks/useRole";

import { ExecutiveHero }      from "./components/ExecutiveHero";
import { TodaysPriorities }   from "./components/TodaysPriorities";
import { AIInsights }         from "./components/AIInsights";
import { RecentAIActivity }   from "./components/RecentAIActivity";
import { InstitutionHealth }  from "./components/InstitutionHealth";
import { FacultyOverview }    from "./components/FacultyOverview";
import { KnowledgeBaseHealth} from "./components/KnowledgeBaseHealth";
import { AISuggestions }      from "./components/AISuggestions";
import { MiniAIWidget }       from "./components/MiniAIWidget";
import { AIHealthWidget }     from "./components/AIHealthWidget";

// Build a one-sentence AI health summary from dashboard data
function buildAISummary(
  modules: number,
  programmes: number,
  findings?: number
): string {
  if (modules > 40) {
    return `Everything looks healthy today. ${findings ?? 7} modules require attention across ${programmes} programmes — your evidence completeness is on track.`;
  }
  if (modules > 10) {
    return `Institution data is loading. ${programmes} programmes are active — run an audit to generate a full health summary.`;
  }
  return "Welcome to AQAA. Start by uploading evidence or triggering your first AI audit.";
}

const DashboardViewInner = memo(function DashboardViewInner() {
  const { data } = useDashboardSummary();
  const {
    isSysAdmin,
    isQAOfficer,
    isDean,
    isHOD,
    isCoordinator,
    isLecturer,
    isStudent,
  } = useRole();

  const healthScore = 87; // deterministic score — wired to real API in Phase 3
  const aiSummary = buildAISummary(data?.modules ?? 0, data?.programmes ?? 0);

  const showPriorities    = isCoordinator;
  const showFaculty       = isDean;
  const showInstHealth    = isQAOfficer;
  const showKBHealth      = isQAOfficer;
  const showAIHealth      = isSysAdmin || isQAOfficer;
  const showRecentActivity= isLecturer;
  const showInsights      = isLecturer;
  const showSuggestions   = isLecturer;
  const showMiniWidget    = isLecturer;

  return (
    <div className="space-y-8">
      {/* Section 1 — Executive Hero (everyone) */}
      <ExecutiveHero healthScore={healthScore} aiSummary={aiSummary} />

      {/* Section 8 — AI Suggestions */}
      {showSuggestions && <AISuggestions />}

      {/* Section 9 — Mini AI Widget */}
      {showMiniWidget && <MiniAIWidget />}

      {/* Section 3 — AI Insights */}
      {showInsights && <AIInsights />}

      {/* Priorities + Recent Activity (side by side on large) */}
      {(showPriorities || showRecentActivity) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {showPriorities    && <TodaysPriorities />}
          {showRecentActivity && <RecentAIActivity />}
        </div>
      )}

      {/* Section 5 — Institution Health + KB Health + AI Health */}
      {(showInstHealth || showKBHealth || showAIHealth) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {showInstHealth && <InstitutionHealth />}
          {showKBHealth   && <KnowledgeBaseHealth />}
          {showAIHealth   && <AIHealthWidget />}
        </div>
      )}

      {/* Section 6 — Faculty Overview */}
      {showFaculty && <FacultyOverview />}
    </div>
  );
});

export function DashboardView() {
  return <DashboardViewInner />;
}
