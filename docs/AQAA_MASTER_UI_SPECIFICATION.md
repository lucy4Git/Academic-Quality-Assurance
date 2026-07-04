# AQAA Master UI Specification

**Document:** AQAA_MASTER_UI_SPECIFICATION.md
**Version:** 1.0
**Date:** 2026-06-19
**Platform:** Academic Quality Assurance Agent (AQAA) — Standalone Enterprise Platform
**Total Screens:** 65

This document contains complete UI specifications for every screen in the AQAA platform. Each specification defines the screen's purpose, roles, component inventory, field definitions, actions, API bindings, validation rules, and acceptance criteria. This document is the authoritative reference for frontend implementation.

---

## Document Structure

| Category | Screens | Screen Numbers |
|----------|---------|----------------|
| Authentication | 2 | 1-2 |
| System / Layout | 3 | 3-5 |
| Dashboard (role-variants) | 7 | 6-12 |
| Institution Management | 4 | 13-16 |
| Faculty Management | 4 | 17-20 |
| Department Management | 4 | 21-24 |
| Programme Management | 4 | 25-28 |
| Module Management | 4 | 29-32 |
| Evidence Management | 4 | 33-36 |
| Audit Management | 7 | 37-43 |
| Findings Management | 3 | 44-46 |
| Reports and Analytics | 5 | 47-51 |
| Accreditation | 2 | 52-53 |
| Notifications | 2 | 54-55 |
| User Management | 4 | 56-59 |
| Settings | 6 | 60-65 |

---

## Global Conventions

### Role Abbreviations
- SA: System Admin (system_admin)
- QA: QA Officer (quality_assurance_officer)
- Dean: Faculty Dean (faculty_dean)
- HOD: Head of Department (head_of_department)
- PC: Programme Coordinator (programme_coordinator)
- Lec: Lecturer (lecturer)
- Stu: Student (student)

### API Base
All API calls target NEXT_PUBLIC_API_BASE_URL/api/v1. Authenticated routes require Authorization: Bearer {access_token} injected by the Axios interceptor from the httpOnly cookie.

### Status Values
- AuditRunStatus: pending, running, completed, failed
- AuditStatus: compliant, needs_attention, non_compliant, critical
- UploadState: pending, scanning, ready, quarantined, failed
- FindingSeverity: critical, high, medium, low, info
- FindingType: missing_document, misclassified, quality_issue, recommendation, info

---

# PART 1 — AUTHENTICATION

---

## Screen 1: Login

**Route:** /login
**Purpose:** Authenticate users with email and password. Redirect to role-appropriate dashboard on success.
**Roles:** All (unauthenticated)

### Layout
Centred card (480px wide) on a navy gradient background. AQAA logo above card. No sidebar or topbar.

### Components
- Logo — AQAA wordmark + icon, centred above card
- Card — white surface, rounded-xl, shadow-lg, p-8
- LoginForm — react-hook-form controlled form
- Input (email) — type email, autocomplete email
- Input (password) — type password, autocomplete current-password
- Button (primary, full-width) — Sign In with loading spinner state
- Link — Forgot password? (Phase 3 feature; renders as disabled text in Phase 2)
- Toast — error notification (destructive variant)

### Fields

| Field | Type | Label | Placeholder | Required |
|-------|------|-------|-------------|----------|
| email | email input | Email address | you@institution.ac.uk | Yes |
| password | password input | Password | (masked) | Yes |

### Actions

| Action | Trigger | Behaviour |
|--------|---------|-----------|
| Sign In | Form submit or Enter key | POST credentials, receive tokens, store in httpOnly cookie, redirect to /dashboard |
| Show/hide password | Eye icon button in password field | Toggle input type between password and text |

### API Endpoints

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| POST | /auth/token | application/x-www-form-urlencoded: username={email}&password={password} | { access_token, refresh_token, token_type } |
| GET | /auth/me | Bearer token (after login) | UserRead (to populate auth store) |

### Validation Rules
- email: required; valid email format (z.string().email())
- password: required; minimum 1 character (server validates complexity on register; login only checks existence)
- On 401: display toast "Invalid email or password. Please try again."
- On 403 (inactive account): display toast "Your account has been disabled. Contact your administrator."
- On network error: display toast "Unable to connect. Check your connection and try again."

### Acceptance Criteria
- Submitting valid credentials sets httpOnly cookies and redirects to /dashboard
- Invalid credentials show a destructive toast without clearing the email field
- Password field has show/hide toggle
- Submit button shows spinner during API call and is disabled to prevent double-submit
- Enter key in either field submits the form
- Page redirects to /dashboard if user is already authenticated
- Focus is placed on the email field on page load
- aria-invalid is set on fields with errors; errors are announced via aria-live

---

## Screen 2: Forbidden (403)

**Route:** /forbidden
**Purpose:** Inform the user they lack permission to access the requested resource. Provide a safe navigation path back.
**Roles:** All (authenticated)

### Layout
Full-page centred layout. AppShell present (sidebar and topbar visible). Content centred in main area.

### Components
- AppShell — standard sidebar and topbar
- PageHeader — no actions
- EmptyState (error variant) — lock icon, heading, description, action button

### Content
- Icon: ShieldX (lucide-react) — 64px, text-destructive
- Heading: "Access Denied"
- Description: "You don't have permission to view this page. If you believe this is an error, contact your system administrator."
- Primary Button: "Go to Dashboard" navigates to /dashboard
- Secondary Link: "Go back" calls router.back()

### Acceptance Criteria
- Page is rendered when a route guard rejects the user's role
- "Go to Dashboard" redirects to /dashboard
- "Go back" returns to the previous page
- Sidebar reflects the user's actual role (correct nav items visible)
- HTTP 403 responses from API calls also redirect here when appropriate

---

# PART 2 — SYSTEM AND LAYOUT

---

## Screen 3: 404 Not Found

**Route:** /not-found (Next.js not-found.tsx)
**Purpose:** Inform the user a requested route or resource does not exist.
**Roles:** All

### Components
- AppShell — if authenticated; bare layout if not
- EmptyState (404 variant) — MapPinOff icon, heading, description, action buttons

### Content
- Icon: MapPinOff — 64px, text-muted-foreground
- Heading: "Page Not Found"
- Description: "The page you're looking for doesn't exist or has been moved."
- Primary Button: "Go to Dashboard" (authenticated) or "Go to Login" (unauthenticated)
- Secondary Link: "Go back"

### Acceptance Criteria
- Rendered by Next.js not-found.tsx for all unmatched routes
- Authenticated users see full AppShell
- Unauthenticated users see minimal layout with no sidebar

---

## Screen 4: Server Error (500)

**Route:** Error boundary — error.tsx
**Purpose:** Handle unexpected runtime errors gracefully without crashing the entire application.
**Roles:** All

### Components
- AppShell — present if session intact
- EmptyState (error variant) — AlertTriangle icon, heading, description, retry button

### Content
- Icon: AlertTriangle — 64px, text-destructive
- Heading: "Something Went Wrong"
- Description: "An unexpected error occurred. Our team has been notified. Please try again or contact support."
- Primary Button: "Try Again" — calls reset() from Next.js error boundary props
- Secondary Button: "Go to Dashboard"

### Acceptance Criteria
- error.tsx catches all unhandled React rendering errors
- "Try Again" calls the Next.js error reset() function
- Error is logged to console in development; sent to Sentry in production (Phase 4)
- User can always navigate away via sidebar or "Go to Dashboard"

---

## Screen 5: Command Palette

**Route:** Overlay — triggered by Cmd+K or Ctrl+K anywhere in the app
**Purpose:** Global keyboard-driven search and navigation across all AQAA entities.
**Roles:** All (authenticated)

### Components
- CommandPalette — full-screen backdrop (bg-black/50) with centred dialog (640px wide)
- CommandInput — search text field, autofocused on open
- CommandGroup — grouped result sections
- CommandItem — individual result row with icon, label, and metadata
- CommandSeparator — between groups
- Badge — entity type label on each result

### Search Groups (in order)
1. Recent — last 5 visited pages (no search query required)
2. Modules — search by code or name
3. Programmes — search by code or name
4. Institutions — search by name or code
5. Audit Runs — search by run ID (first 8 chars) or module code
6. Findings — search by title
7. Users — search by name or email (SA only)

### Actions

| Action | Trigger | Behaviour |
|--------|---------|-----------|
| Open palette | Cmd+K or Ctrl+K | Mount overlay, focus input |
| Close palette | Escape or click backdrop | Unmount overlay, return focus to trigger |
| Navigate to result | Enter on selected item or click item | Navigate to resource route; close palette |
| Cycle results | Up or Down arrow keys | Move selection highlight |

### API Endpoints
- GET /modules?search={query}&limit=5
- GET /programmes?search={query}&limit=5
- GET /institutions?search={query}&limit=5
- GET /audits?search={query}&limit=5

### Acceptance Criteria
- Opens on Cmd+K or Ctrl+K from any authenticated page
- Closes on Escape and returns focus to the previously focused element
- Search results debounce 200ms before API call
- Each result navigates to the correct detail page
- Fully keyboard navigable (no mouse required)
- aria-label="Global command palette" on dialog; results use role="option"
- Recent items shown without typing (sourced from local state, no API call)

---

# PART 3 — DASHBOARDS

---

## Screen 6: System Admin Dashboard

**Route:** /dashboard (rendered when role === system_admin)
**Purpose:** Platform-wide health overview. All institutions visible. System status, user activity, audit volume.
**Roles:** SA

### Components
- PageHeader — "Platform Dashboard", subtitle: current date and "System Administrator"
- KpiRow — 4x StatCard
- Card (Platform Health) — service status indicators
- ComplianceByInstitutionChart — horizontal bar chart (Recharts BarChart)
- ActivityFeed — scrollable event list
- RecentAuditRunsTable — DataTable (last 10 runs, all institutions)
- StorageUsageGauge — radial gauge

### KPI Cards

| Card | Value Source | Delta | Click Target |
|------|-------------|-------|-------------|
| Institutions | Count of all institutions | None | /institutions |
| Active Modules | Count of all modules | None | /modules |
| Users (today) | Distinct logins today | vs yesterday | /users |
| Storage Used | Total file storage | vs last week | /settings/storage |

### Platform Health Widget
Rows: PostgreSQL, Redis, Qdrant, Backend API, Storage.
Status from GET /health. Each row: green dot (healthy) or red dot (unhealthy) plus service name.

### Chart: Compliance by Institution
Horizontal bar per institution. Value = average compliance_score from all completed audit_runs. Tooltip shows institution name, avg score, module count.

### Recent Audit Runs Table
Columns: Module Code, Agent, Status Badge, Score, Institution, Triggered By, Created At, Actions.
Row action: "View Report" to /audits/{id}/report.
Pagination: 10 rows, "View All" link to /audits.

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /health | Service status |
| GET | /institutions | Institution list and compliance averages |
| GET | /audits?limit=10 | Recent audit runs |
| GET | /dashboard | Aggregated KPIs (Phase 2 backend required) |

### Acceptance Criteria
- All 4 KPI cards display correct values
- Compliance bars render for each institution
- Service health indicators reflect actual API availability
- Recent audits table is sorted by created_at descending
- All chart tooltips display on hover and are keyboard-accessible
- Page loads in under 2 seconds (skeleton shown during fetch)

---

## Screen 7: QA Officer Dashboard

**Route:** /dashboard (rendered when role === quality_assurance_officer)
**Purpose:** Institution-scoped compliance overview. Primary operational view for the quality office.
**Roles:** QA

### Components
- PageHeader — "QA Dashboard - {Institution Name}", actions: [Export Report] [Trigger Audit]
- KpiRow — 4x StatCard
- ComplianceByFacultyChart — horizontal bar chart
- FindingsBySeverityChart — donut chart (Recharts PieChart with innerRadius)
- ComplianceTrendChart — multi-line chart (one line per faculty, last 6 cycles)
- ModulesRequiringAttentionTable — DataTable
- OpenFindingsTable — DataTable

### KPI Cards

| Card | Value | Delta | Click Target |
|------|-------|-------|-------------|
| Avg Compliance Score | Mean of all module scores (institution-scoped) | vs last cycle | /reports/compliance |
| Critical Findings | Count of open findings with severity=critical | vs last week | /findings?severity=critical |
| Pending Audits | Count of runs with run_status=pending or running | None | /audits?status=pending |
| Modules Below 50% | Count of modules with last score < 50 | vs last month | /modules?below_threshold=true |

### Compliance Trend Chart
Line chart. X-axis: last 6 months formatted as MMM YYYY. Y-axis: 0-100. One line per faculty (colour-coded). Hover tooltip: month, faculty, score.

### Open Findings Table
Columns: Severity Badge, Module, Finding Title, Agent, Days Open, Action.
Row action: "Resolve" opens ResolveFindingPanel slide-over.

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /dashboard | KPI aggregates |
| GET | /faculties?institution_id={id} | Faculty list for chart |
| GET | /audits?institution_id={id}&limit=50 | Compliance data |
| GET | /findings?institution_id={id}&is_resolved=false | Open findings |

### Acceptance Criteria
- All data is scoped to the QA Officer's institution; no cross-institution data leaks
- "Export Report" triggers PDF generation of compliance summary
- "Trigger Audit" opens TriggerAuditDialog (Screen 38)
- Clicking a KPI card navigates to the corresponding filtered list page
- Empty state shown for each widget when no data exists

---

## Screen 8: Faculty Dean Dashboard

**Route:** /dashboard (rendered when role === faculty_dean)
**Purpose:** Faculty-scoped compliance view. Compare departments, highlight critical findings.
**Roles:** Dean

### Components
- PageHeader — "Faculty Dashboard - {Faculty Name}"
- KpiRow — 4x StatCard
- DepartmentComparisonChart — horizontal bar (departments in user's faculty)
- ModuleHealthHeatmap — grid of module cards coloured by compliance score
- CriticalFindingsList — scrollable card list, most recent first

### KPI Cards

| Card | Value | Click Target |
|------|-------|-------------|
| Faculty Avg Score | Mean of department averages | /reports/compliance |
| Departments Below Avg | Count of departments with score below faculty avg | /departments |
| Open Findings | Count open findings in faculty | /findings |
| Modules Audited | Count of modules with at least 1 completed run / total | /modules |

### Module Health Heatmap
3-column responsive grid. Each cell = one module. Background: red (below 50%), orange (50-69%), amber (70-89%), green (90+), grey (never audited). Cell content: module code plus score. Click to /modules/{id}.

### API Endpoints
- GET /departments?faculty_id={id}
- GET /modules?faculty_id={id}
- GET /findings?faculty_id={id}&is_resolved=false&severity=critical

### Acceptance Criteria
- All data scoped to Dean's faculty only
- Heatmap renders for all modules in faculty
- Clicking module cell navigates to module detail
- Critical findings list sorted by created_at descending

---

## Screen 9: Head of Department Dashboard

**Route:** /dashboard (rendered when role === head_of_department)
**Purpose:** Department module compliance matrix. Identify lecturers with zero uploads. Surface missing document categories.
**Roles:** HOD

### Components
- PageHeader — "Department Dashboard - {Department Name}"
- KpiRow — 4x StatCard
- ModuleComplianceMatrixTable — full-width DataTable
- LecturerUploadActivityChart — horizontal bar per lecturer (30-day upload count)
- MissingDocumentCategoryWidget — ranked list of most-missing categories

### KPI Cards

| Card | Value | Click Target |
|------|-------|-------------|
| Dept Avg Compliance | Mean of module scores | /reports/compliance |
| Lecturers With 0 Uploads | Count of lecturers with 0 files uploaded in 30 days | /files |
| Modules Not Audited | Count of modules with no completed run | /audits |
| Critical Findings | Count open critical findings in department | /findings?severity=critical |

### Module Compliance Matrix Table
Columns: Module Code, Module Name, Lecturer, Compliance Score, Docs Present / Total, Missing Docs, Last Audit, Actions.
Actions per row: "View Module" and "Trigger Audit".

### Missing Document Category Widget
Ranked list: each row = document category + count of modules missing it.
Example: "Assessment Brief — missing in 3 modules" with a mini bar.

### API Endpoints
- GET /modules?department_id={id}
- GET /files?department_id={id}&uploaded_after={30_days_ago}
- GET /findings?department_id={id}&is_resolved=false

### Acceptance Criteria
- Module matrix shows all modules in HOD's department
- "Trigger Audit" on a matrix row opens TriggerAuditDialog pre-filled with module
- Lecturer activity bars show zero for lecturers with no uploads
- Missing category widget is sorted descending by count

---

## Screen 10: Programme Coordinator Dashboard

**Route:** /dashboard (rendered when role === programme_coordinator)
**Purpose:** Programme-level compliance view with per-module breakdown and quick audit triggers.
**Roles:** PC

### Components
- PageHeader — "Programme Dashboard - {Programme Name} - {Academic Year}", action: [Trigger All Audits]
- KpiRow — 4x StatCard
- ModuleComplianceProgressList — vertical list of module cards with compliance bars
- EvidenceCoverageRingChart — donut showing present vs missing docs across all programme modules
- LastAuditSummaryCard — last Programme Review result

### KPI Cards

| Card | Value |
|------|-------|
| Programme Avg Score | Mean of module compliance scores |
| Evidence Coverage | Percentage of required docs present across all modules |
| Last Audit Date | Date of most recent completed run on any module |
| Open Findings | Count open findings across all programme modules |

### Module Compliance Progress List
Each module: module code + name + horizontal progress bar + score + status badge + [Run Audit] button.
Button triggers TriggerAuditDialog pre-filled with that module.

### API Endpoints
- GET /modules?programme_id={id}
- GET /audits?programme_id={id}&limit=20
- GET /programme-review-audits/{latest_run_id} (last programme review)

### Acceptance Criteria
- "Trigger All Audits" opens dialog with all programme modules pre-selected
- Each module row's "Run Audit" button pre-fills dialog with that module
- Evidence coverage ring updates when new files are uploaded

---

## Screen 11: Lecturer Dashboard

**Route:** /dashboard (rendered when role === lecturer)
**Purpose:** Personal module compliance with an actionable document upload checklist.
**Roles:** Lec

### Components
- PageHeader — "My Module: {Module Code} — {Module Name}"
- KpiRow — 4x StatCard
- DocumentUploadChecklist — full checklist with per-category upload buttons
- LastAuditResultCard — most recent audit result with score and agent name
- UploadPromptBanner — sticky banner if critical documents are missing

### KPI Cards

| Card | Value | Click Target |
|------|-------|-------------|
| Compliance Score | Last audit compliance score | /audits/{last_run_id}/report |
| Documents Present | Count present / total required | /files?module_id={id} |
| Documents Missing | Count of required categories absent | /modules/{id}/upload |
| Open Findings | Count of unresolved findings on module | /findings?module_id={id} |

### Document Upload Checklist
Each row: status icon (green tick or red cross) + category label + file name if present + upload date if present + [Upload] button on missing items.
Clicking [Upload] navigates to /modules/{id}/upload with category pre-selected.

### Upload Prompt Banner
Shown when 1 or more critical documents are missing.
Content: "Critical documents are missing. Upload them now to improve your compliance score."
Action: [Upload Now] to /modules/{id}/upload.

### API Endpoints
- GET /modules/{id}
- GET /files?module_id={id}
- GET /audits/modules/{id}/latest
- GET /findings?module_id={id}&is_resolved=false

### Acceptance Criteria
- Checklist shows all required document categories
- Present documents show filename and upload date
- Missing documents show [Upload] button that pre-selects the category
- Upload prompt banner is dismissed once all critical documents are present
- If lecturer has multiple modules, a module selector appears in the page header

---

## Screen 12: Student Dashboard

**Route:** /dashboard (rendered when role === student)
**Purpose:** Read-only transparency view. Students see their programme's quality status.
**Roles:** Stu

### Components
- PageHeader — "Programme Quality Overview - {Programme Name}"
- ProgrammeQualityStatusCard — status banner with score and AuditStatus label
- ModuleComplianceList — read-only list of modules with compliance badges
- InfoCallout — explanatory note about the purpose of this data

### Info Callout Text
"This information is provided for transparency. Compliance scores reflect how completely academic quality evidence has been documented. If you have concerns, contact your Programme Coordinator."

### API Endpoints
- GET /programmes/{id}
- GET /modules?programme_id={id}
- GET /audits?programme_id={id}&limit=5

### Acceptance Criteria
- Student cannot trigger audits, upload files, or resolve findings
- All action buttons are hidden (not just disabled)
- Info callout is always visible
- Module list is sorted alphabetically by code

---

# PART 4 — INSTITUTION MANAGEMENT

---

## Screen 13: Institutions List

**Route:** /institutions
**Purpose:** View and manage all registered institutions. Entry point for institution-level drill-down.
**Roles:** SA, QA

### Components
- PageHeader — "Institutions", actions: [+ Add Institution] (SA only)
- DataTableToolbar — search by name or code; filter by country
- DataTable — institution rows
- EmptyState — shown when no institutions exist
- ConfirmDialog — for delete action

### Table Columns

| Column | Type | Sortable | Filterable |
|--------|------|----------|-----------|
| Name | text + logo thumbnail | Yes | No |
| Code | badge | Yes | No |
| Country | text | Yes | Yes |
| Faculties | number | No | No |
| Modules | number | No | No |
| Avg Compliance | progress bar + % | Yes | No |
| Open Findings | number badge | No | No |
| Created | date | Yes | No |
| Actions | kebab menu | No | No |

### Row Actions
- "View Details" to /institutions/{id}
- "Edit" to /institutions/{id}/edit (SA only)
- "Delete" to ConfirmDialog then DELETE /institutions/{id} (SA only)

### API Endpoints
- GET /institutions

### Acceptance Criteria
- SA sees all institutions; QA sees only their own institution
- Search filters by name and code
- Compliance bar is colour-coded by score range
- Delete is SA-only; not rendered for QA role
- Empty state shown with "Add your first institution" CTA when list is empty

---

## Screen 14: Institution Detail

**Route:** /institutions/[id]
**Purpose:** Full institution profile with compliance overview, faculty list, and reports.
**Roles:** SA, QA

### Tabs
- Overview — Summary card, compliance gauge, faculty count, recent activity
- Faculties — List of faculties with campus and compliance score
- Compliance — Compliance trend chart; faculty breakdown bar chart
- Findings — All open findings scoped to this institution
- Reports — Available reports with export buttons
- Settings — Institution metadata edit form (SA only)

### Overview Tab
- Institution logo, name, code, country, address
- Stat row: Faculties, Departments, Programmes, Modules, Users, Files
- Recent activity timeline (last 5 audit runs)

### Faculties Tab
Columns: Faculty Name, Code, Campus, Departments, Modules, Avg Compliance, Actions.
Row action: "View Faculty" to /faculties/{id}.

### API Endpoints
- GET /institutions/{id}
- GET /faculties?institution_id={id}
- GET /findings?institution_id={id}&is_resolved=false

### Acceptance Criteria
- Breadcrumb shows: Home / Institutions / {Institution Name}
- Tabs maintain their scroll position when switching
- QA Officer sees all tabs except Settings
- Export Report generates PDF of compliance summary

---

## Screen 15: Create Institution

**Route:** /institutions/new
**Purpose:** Register a new institution in the platform.
**Roles:** SA

### Fields

| Field | Type | Label | Required | Constraints |
|-------|------|-------|----------|-------------|
| name | text | Institution Name | Yes | 2-255 chars |
| code | text | Institution Code | Yes | 2-20 chars, uppercase, unique |
| country | text | Country | No | max 100 chars |
| address | textarea | Address | No | max 500 chars |
| logo_url | url input | Logo URL | No | valid URL format |

### API Endpoints
- POST /institutions

### Validation Rules
- name: required, 2-255 chars
- code: required, 2-20 chars, uppercase alphanumeric and hyphen only
- On 409 (duplicate code): show inline field error "This institution code is already in use."

### Acceptance Criteria
- Form is accessible via keyboard only
- Code field auto-uppercases input on blur
- Successful creation shows success toast "Institution created" and redirects to /institutions/{new_id}
- 409 conflict shows inline field error on code field
- Cancel returns to institutions list without any API call

---

## Screen 16: Edit Institution

**Route:** /institutions/[id]/edit
**Purpose:** Update an existing institution's metadata.
**Roles:** SA

### Fields
Same as Screen 15. All fields pre-populated from GET /institutions/{id}.

### Actions

| Action | Trigger | Behaviour |
|--------|---------|-----------|
| Save Changes | Submit | PATCH /institutions/{id} then success toast |
| Delete Institution | Delete button | ConfirmDialog warning then DELETE /institutions/{id} then redirect to /institutions |
| Cancel | Cancel | Navigate to /institutions/{id} |

### API Endpoints
- GET /institutions/{id}
- PATCH /institutions/{id}
- DELETE /institutions/{id}

### Acceptance Criteria
- Form is pre-populated with current values on load
- PATCH only sends changed fields
- Delete shows a confirmation dialog with institution name and cascade warning
- After delete, user is redirected to /institutions with a "Institution deleted" toast

---

# PART 5 — FACULTY MANAGEMENT

---

## Screen 17: Faculties List

**Route:** /faculties
**Purpose:** Browse faculties scoped to the user's institution or all institutions for SA.
**Roles:** SA, QA, Dean

### Table Columns

| Column | Type | Sortable |
|--------|------|----------|
| Name | text | Yes |
| Code | badge | Yes |
| Institution | text (SA only) | Yes |
| Campus | badge | Yes |
| Departments | number | No |
| Modules | number | No |
| Avg Compliance | progress bar | Yes |
| Dean | text | No |
| Actions | kebab | No |

### Row Actions
- "View Details" to /faculties/{id}
- "Edit" to /faculties/{id}/edit (SA, QA)
- "Delete" to confirm then DELETE /faculties/{id} (SA only)

### Acceptance Criteria
- Dean sees only faculties in their institution
- QA Officer sees only their institution's faculties
- SA sees all faculties with Institution column visible

---

## Screen 18: Faculty Detail

**Route:** /faculties/[id]
**Purpose:** Faculty profile with department breakdown, compliance chart, and findings.
**Roles:** SA, QA, Dean

### Tabs
- Overview — stats: departments, modules, avg compliance, dean name, campus
- Departments — table of departments with compliance scores
- Modules — all modules in this faculty (cross-department)
- Compliance — faculty compliance trend chart and department bar chart
- Findings — faculty-scoped open findings

### API Endpoints
- GET /faculties/{id}
- GET /departments?faculty_id={id}
- GET /modules?faculty_id={id}
- GET /findings?faculty_id={id}&is_resolved=false

### Acceptance Criteria
- Breadcrumb: Home / Institutions / {Institution} / Faculties / {Faculty}
- Campus shown as a badge in the overview header
- Departments tab compliance bars link to department detail pages

---

## Screen 19: Create Faculty

**Route:** /faculties/new
**Purpose:** Create a new faculty within an institution.
**Roles:** SA, QA

### Fields

| Field | Type | Label | Required | Constraints |
|-------|------|-------|----------|-------------|
| institution_id | select (searchable) | Institution | Yes (SA) / hidden for QA (auto-set) | Must be valid institution UUID |
| name | text | Faculty Name | Yes | 2-255 chars |
| code | text | Faculty Code | Yes | 2-20 chars, unique within institution |
| campus | text | Campus | No | max 100 chars |
| dean_id | select (searchable) | Faculty Dean | No | User with role faculty_dean in same institution |

### API Endpoints
- POST /faculties
- GET /institutions (to populate institution selector, SA only)
- GET /users?role=faculty_dean&institution_id={id} (to populate dean selector)

### Validation Rules
- institution_id: required for SA; auto-set to user's institution for QA
- code: unique within institution (server returns 409 on conflict)

### Acceptance Criteria
- QA Officer's institution is auto-set and the field is hidden
- Dean selector filters to faculty_dean role users within the selected institution
- 409 on code conflict shows inline field error

---

## Screen 20: Edit Faculty

**Route:** /faculties/[id]/edit
**Purpose:** Update faculty metadata.
**Roles:** SA, QA

Same fields as Screen 19 with pre-populated values.
Additional Action: Delete Faculty (SA only) with cascade warning.

### API Endpoints
- GET /faculties/{id}
- PATCH /faculties/{id}
- DELETE /faculties/{id} (SA only)

---

# PART 6 — DEPARTMENT MANAGEMENT

---

## Screen 21: Departments List

**Route:** /departments
**Purpose:** Browse departments. HOD sees their own department prominently.
**Roles:** SA, QA, Dean, HOD

### Table Columns

| Column | Type | Visible to |
|--------|------|-----------|
| Name | text | All |
| Code | badge | All |
| Faculty | text | SA, QA, Dean |
| Programmes | number | All |
| Modules | number | All |
| Avg Compliance | progress bar | All |
| Head | text | All |
| Actions | kebab | All |

### API Endpoints
- GET /departments (scoped by faculty/institution based on role)

---

## Screen 22: Department Detail

**Route:** /departments/[id]
**Purpose:** Department hub with module compliance matrix and evidence gap analysis.
**Roles:** SA, QA, Dean, HOD

### Tabs
- Overview — stats summary
- Module Board — module compliance matrix table
- Evidence Gap — cross-module document category presence matrix
- Lecturers — lecturer list with 30-day upload activity bars
- Findings — department-scoped open findings
- Reports — department compliance report export

### Evidence Gap Matrix
Rows = modules, Columns = document categories.
Cell: tick (green) = file in ready state exists for that category; cross (red) = missing; dash = not applicable.
Export button: "Export as CSV".

### API Endpoints
- GET /departments/{id}
- GET /modules?department_id={id}
- GET /files?department_id={id}
- GET /findings?department_id={id}&is_resolved=false

### Acceptance Criteria
- Evidence gap matrix renders for all modules and all document categories
- Cells are colour-coded by presence status
- CSV export of gap matrix downloads correctly
- Lecturer upload activity bars show 30-day file upload count per lecturer

---

## Screen 23: Create Department

**Route:** /departments/new
**Purpose:** Create a new department within a faculty.
**Roles:** SA, QA, Dean

### Fields

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| faculty_id | select (searchable) | Yes | Valid faculty UUID in user's institution |
| name | text | Yes | 2-255 chars |
| code | text | Yes | 2-20 chars, unique within faculty |
| head_id | select (searchable) | No | User with role head_of_department in same institution |

### API Endpoints
- POST /departments
- GET /faculties?institution_id={id} (to populate faculty selector)

---

## Screen 24: Edit Department

**Route:** /departments/[id]/edit
**Purpose:** Update department metadata.
**Roles:** SA, QA, Dean

Same fields as Screen 23, pre-populated.

### API Endpoints
- GET /departments/{id}
- PATCH /departments/{id}
- DELETE /departments/{id} (SA only)

---

# PART 7 — PROGRAMME MANAGEMENT

---

## Screen 25: Programmes List

**Route:** /programmes
**Purpose:** Browse programmes. Students see their enrolled programme only.
**Roles:** All

### Table Columns

| Column | Type | Visible to |
|--------|------|-----------|
| Name | text | All |
| Code | badge | All |
| Department | text | SA, QA, Dean, HOD |
| Level | badge (UG/PG/Doc) | All |
| Modules | number | All |
| Avg Compliance | progress bar | SA, QA, Dean, HOD, PC, Lec |
| Coordinator | text | SA, QA, Dean, HOD, PC |
| Actions | kebab | SA, QA, Dean, HOD |

### API Endpoints
- GET /programmes (scoped by department/faculty/institution based on role)

---

## Screen 26: Programme Detail

**Route:** /programmes/[id]
**Purpose:** Programme hub with module breakdown, audit history, and programme review panel.
**Roles:** All

### Tabs
- Overview — stats: modules, avg compliance, level, coordinator
- Modules — module list with compliance progress bars and per-module audit trigger
- Audit History — Programme Review audit runs (programme-scoped)
- Compliance — module compliance bar chart
- Settings — edit programme (SA, QA, Dean, HOD, PC only)

### Modules Tab Special Feature
Right-side sticky panel (desktop): "Latest Programme Review" card showing last run status, score, finding count, completion date, and action buttons.

### API Endpoints
- GET /programmes/{id}
- GET /modules?programme_id={id}
- GET /programme-review-audits/programmes/{id}/latest
- GET /programme-review-audits/programmes/{id}/history

### Acceptance Criteria
- Students see Overview and Modules tabs only (read-only)
- Programme Review panel updates when a new review completes
- Module compliance bars link to individual module pages

---

## Screen 27: Create Programme

**Route:** /programmes/new
**Purpose:** Create a new programme within a department.
**Roles:** SA, QA, Dean, HOD

### Fields

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| department_id | select (searchable) | Yes | Valid department UUID |
| name | text | Yes | 2-255 chars |
| code | text | Yes | 2-20 chars, unique within department |
| level | select | Yes | undergraduate, postgraduate, or doctoral |
| coordinator_id | select (searchable) | No | User with programme_coordinator role |

### Validation Rules
- level: must be lowercase enum value (undergraduate, postgraduate, doctoral)
- code: unique within department (409 on conflict)

### API Endpoints
- POST /programmes

---

## Screen 28: Edit Programme

**Route:** /programmes/[id]/edit
**Purpose:** Update programme metadata.
**Roles:** SA, QA, Dean, HOD

Same as Screen 27 with pre-populated values.

### API Endpoints
- GET /programmes/{id}
- PATCH /programmes/{id}
- DELETE /programmes/{id} (SA, QA only)

---

# PART 8 — MODULE MANAGEMENT

---

## Screen 29: Modules List

**Route:** /modules
**Purpose:** Browse modules. Lecturers see their assigned modules. Students see modules in their programme.
**Roles:** All

### Table Columns

| Column | Visible to |
|--------|-----------|
| Code | All |
| Name | All |
| Programme | SA, QA, Dean, HOD, PC |
| Academic Year | All |
| Semester | All |
| Credits | All |
| Lecturer | SA, QA, Dean, HOD, PC |
| Last Compliance Score | SA, QA, Dean, HOD, PC, Lec |
| Last Audit | SA, QA, Dean, HOD, PC, Lec |
| Status Badge | All |
| Actions | SA, QA, Dean, HOD, PC |

### Filters
- Search by code or name
- Academic Year (select)
- Programme (select, role-scoped)
- Compliance threshold
- Semester

### Row Actions
- "View Module" to /modules/{id}
- "Upload Evidence" to /modules/{id}/upload
- "Trigger Audit" opens TriggerAuditDialog (SA, QA, Dean, HOD, PC)
- "Edit" to /modules/{id}/edit (SA, QA, Dean, HOD, PC)

### API Endpoints
- GET /modules (role-scoped)

---

## Screen 30: Module Detail

**Route:** /modules/[id]
**Purpose:** Central hub for a module. Evidence management, audit triggers, compliance score, and findings all accessible from one place.
**Roles:** All

### Page Header
Module code (badge) + Module Name, Programme name, Semester, Academic Year, Credits, Lecturer.
Actions: [Upload Evidence] (role-scoped), [Run Audit] (PC+), kebab menu (edit, delete).

### Tabs
1. Overview — compliance score gauge, document checklist, audit agent grid
2. Evidence — file library scoped to this module
3. Audits — all audit runs for this module
4. Findings — all findings for this module
5. Settings — edit module form (SA, QA, Dean, HOD, PC only)

### Overview Tab Layout

Left column (8/12):
- Compliance Score Card: large gauge + score value + AuditStatus badge + "View Last Report" link
- Document Checklist Card: 22-category checklist with tick/cross per category + upload link on missing items

Right column (4/12, sticky on scroll):
- Latest Audit Summary: agent name + run date + score + findings count
- Quick Actions: [Upload Evidence] and [Run All Agents]

### Audit Agent Grid
Two rows of four AuditAgentCard components.
Each card: agent icon, agent name, last score (or "Never run"), last run status badge, [Run] button.
Agents: Module Folder Audit, Assessment Compliance, Moderation Compliance, Attendance Compliance, Evidence Verification, Outcome Alignment, Accreditation Readiness.

### Evidence Tab
File table: Filename, Category, Size, Version, Upload State, Uploaded By, Date, Actions.
File actions kebab: Preview, Download, Change Category, View Versions, Delete.
Toolbar: [+ Upload File] + filter by category + filter by upload state + search by filename.

### Audits Tab
All audit runs for this module.
Columns: Agent, Status Badge, Compliance Score, Audit Status, Findings, Triggered By, Started, Completed, Actions.
Row actions: "View Report" (if completed).

### Findings Tab
All findings (open and resolved) for this module.

### API Endpoints
- GET /modules/{id}
- GET /files?module_id={id}
- GET /audits/modules/{id}/history
- GET /audits/modules/{id}/latest
- GET /findings?module_id={id}

### Acceptance Criteria
- Overview tab loads without navigating away
- Audit agent grid shows real last-run scores (skeleton while loading)
- [Run] on any agent card opens TriggerAuditDialog pre-filled with that agent and this module
- [Run All Agents] opens dialog with all 7 module-scoped agents pre-checked
- File upload state badges update in real-time
- Students see Tabs 1, 2, 4 in read-only mode (no upload buttons, no run buttons)

---

## Screen 31: Create Module

**Route:** /modules/new
**Purpose:** Create a new module within a programme.
**Roles:** SA, QA, Dean, HOD, PC

### Fields

| Field | Type | Label | Required | Constraints |
|-------|------|-------|----------|-------------|
| programme_id | select (searchable) | Programme | Yes | Valid programme UUID |
| name | text | Module Name | Yes | 2-255 chars |
| code | text | Module Code | Yes | 2-50 chars |
| credits | number | Credits | Yes | 0-240 integer |
| semester | text | Semester | Yes | e.g. "Semester 1" |
| academic_year | text | Academic Year | Yes | Pattern YYYY/YYYY e.g. "2025/2026" |
| lecturer_id | select (searchable) | Assigned Lecturer | No | User with lecturer role in same institution |

### Validation Rules
- academic_year: regex matches YYYY/YYYY; second year must be first year + 1
- credits: integer, 0-240
- code: unique within programme and academic year (server returns 409 on conflict)

### API Endpoints
- POST /modules
- GET /programmes (programme selector)
- GET /users?role=lecturer&institution_id={id} (lecturer selector)

---

## Screen 32: Edit Module

**Route:** /modules/[id]/edit
**Purpose:** Update module metadata including lecturer assignment.
**Roles:** SA, QA, Dean, HOD, PC

Same fields as Screen 31 with pre-populated values.

### API Endpoints
- GET /modules/{id}
- PATCH /modules/{id}
- DELETE /modules/{id} (SA, QA only) with cascade warning

---

# PART 9 — EVIDENCE MANAGEMENT

---

## Screen 33: File Library

**Route:** /files
**Purpose:** Institution-scoped searchable file library. Browse, filter, and manage all uploaded documents.
**Roles:** SA, QA, Dean, HOD, PC, Lec

### Components
- PageHeader — "File Library", actions: [+ Upload Evidence]
- DataTableToolbar — search by filename; filter by module, category, upload state, date range
- DataTable — file rows

### Table Columns

| Column | Type | Sortable | Filterable |
|--------|------|----------|-----------|
| Filename | text with file type icon | Yes | No |
| Category | badge | No | Yes |
| Module | text | Yes | Yes |
| Size | formatted bytes | Yes | No |
| Version | number | No | No |
| Upload State | badge | No | Yes |
| Uploaded By | text | No | No |
| Date | date | Yes | Yes |
| Actions | kebab | No | No |

### File Row Actions
- "Preview" — opens FilePreview lightbox (PDF and images only)
- "Download" — GET /files/{id}/download
- "View Versions" — navigates to /files/{id}/versions
- "Change Category" — inline category selector
- "Delete" — soft-delete confirm dialog then DELETE /files/{id}

### Acceptance Criteria
- Lecturer sees only files from their assigned modules
- Upload state badge "Scanning" pulses to indicate in-progress
- Quarantined files show a red badge with tooltip "This file was blocked by virus scan"
- PDF preview opens in a lightbox without downloading the file
- Deleted files are soft-deleted and hidden from list by default

---

## Screen 34: Upload Evidence

**Route:** /modules/[id]/upload
**Purpose:** Upload one or more documents to a module folder. The primary evidence collection interface.
**Roles:** SA, QA, Dean, HOD, PC, Lec

### Components
- PageHeader — "Upload Evidence - {Module Code} — {Module Name}", action: [View File Library]
- CategorySelect — grouped two-level dropdown (group then specific category)
- DropzoneUpload — drag-and-drop zone with file browser fallback
- FileUploadQueue — list of queued/uploading/completed files
- Input (description) — optional description textarea
- Button (primary) — "Upload All Files"
- Button (secondary) — "Cancel"
- Toast — success/error notifications

### Category Select Groups

| Group | Categories |
|-------|-----------|
| Course Materials | Course Outline, Study Guide, Learning Outcomes, Weekly Plan |
| Assessment | Assessment Plan, Assessment Brief, Assessment Rubric, Assessment Memo, Exam Paper, Practical Task |
| Moderation | Internal Moderation, External Moderation, Moderation Evidence |
| Marked Work | Marked Sample, Mark Sheet |
| Attendance | Attendance Register, Tutorial Attendance, Practical Attendance, LMS Participation |
| Feedback | Student Feedback |
| Accreditation | Accreditation Evidence |
| Other | Other |

### Dropzone Behaviour
- Accept: .pdf, .docx, .doc, .xlsx, .xls, .pptx, .ppt, .jpg, .jpeg, .png
- Reject: other formats with inline error message in dropzone
- Max file size: 50 MB
- Multiple files in one drop accepted
- Each file gets a row in the upload queue

### Upload Queue Row
File type icon, Filename, File size, Progress bar or status badge, Remove button.
Progress bar: 0-100% during upload (XMLHttpRequest).
After upload: status badge (Scanning then Ready or Quarantined).

### Post-Upload Prompt
After all files reach ready state: banner appears: "All files uploaded successfully. Would you like to run an audit now?" with [Run Audit] button.

### Fields

| Field | Label | Required | Notes |
|-------|-------|----------|-------|
| category | Document Category | Yes | Applied to all files in the current batch |
| file | Files | Yes | 1-20 files per upload session |
| description | Description | No | Applied to all files in batch |

### API Endpoints
- POST /files/upload — multipart: file, module_id, category, description
- GET /files/{id} — poll for upload state after upload completes

### Validation Rules
- At least one file required before submit
- Category must be selected before any file is added to queue
- File size: client-side validation before upload starts; error message per file
- File type: client-side MIME type check; error inline in dropzone

### Acceptance Criteria
- Drag-and-drop works on desktop; file browse picker works on mobile
- Progress bars update in real-time during upload
- Upload state transitions are reflected without page refresh
- Quarantined files show warning with explanation
- Category selection is required; attempt to drop files without selecting category shows inline error
- Post-upload audit prompt opens TriggerAuditDialog with module pre-filled

---

## Screen 35: File Detail

**Route:** /files/[id]
**Purpose:** Full metadata view of a single uploaded file including processing status, checksum, and version history link.
**Roles:** All (scoped by module access)

### Components
- PageHeader — filename, actions: [Download] [Delete] (role-scoped)
- Card (Metadata) — all file properties
- Card (Processing) — document extraction and classification status
- Button — "View Version History" to /files/{id}/versions

### Metadata Display

| Field | Value |
|-------|-------|
| Category | Badge |
| Module | Link to /modules/{id} |
| Size | Formatted bytes |
| MIME Type | Text |
| Version | Number |
| Checksum (SHA-256) | Monospace, copyable |
| Upload State | Badge |
| Uploaded By | User name |
| Uploaded At | Formatted date |

### Processing Status Display

| Field | Value |
|-------|-------|
| Processing Status | Badge |
| Word Count | Number |
| Page Count | Number |
| Language Detected | ISO code |
| Classification | Detected category |
| Classification Confidence | Percentage |

### API Endpoints
- GET /files/{id}
- GET /files/{id}/preview

---

## Screen 36: Version History

**Route:** /files/[id]/versions
**Purpose:** View all uploaded versions of a file with download links for each version.
**Roles:** SA, QA, HOD, PC, Lec

### Table Columns

| Column | Type |
|--------|------|
| Version | number badge (v1, v2...) |
| Original Filename | text |
| Size | formatted bytes |
| Checksum (SHA-256) | monospace (truncated with copy) |
| Uploaded By | text |
| Uploaded At | date |
| Actions | Download button |

### API Endpoints
- GET /files/{id}/versions
- GET /files/{id}/versions/{version_number}/download

### Acceptance Criteria
- Versions listed newest first
- Current version is highlighted with a "Current" badge
- Each version has its own download link

---

# PART 10 — AUDIT MANAGEMENT

---

## Screen 37: Audit Centre

**Route:** /audits
**Purpose:** Global view of all audit runs for the user's institution. Monitor active audits, browse history, and navigate to reports.
**Roles:** SA, QA, Dean, HOD, PC, Lec

### Components
- PageHeader — "Audit Centre", actions: [+ Trigger Audit] (PC+)
- Tabs — Active, Completed, Failed, All
- DataTableToolbar — filter by agent, module, date range
- DataTable — audit run rows
- AuditProgressCard — shown for each active run (live polling)

### Table Columns

| Column | Type | Sortable |
|--------|------|----------|
| Agent | badge with icon | No |
| Module or Programme | text and link | Yes |
| Status | badge | No |
| Compliance Score | progress bar and % | Yes |
| Audit Status | badge | No |
| Findings | number | No |
| Triggered By | text | No |
| Started | date/time | Yes |
| Completed | date/time | Yes |
| Actions | kebab | No |

### Row Actions
- "View Report" to /audits/{id}/report (completed runs only)
- "View Run" to /audits/{id}
- "Trigger Again" opens TriggerAuditDialog pre-filled with same module and agent

### API Endpoints
- GET /audits (institution-scoped for non-SA)
- Polling for active runs: GET /audits/{id} every 3 seconds per active run

### Acceptance Criteria
- Active runs section auto-updates without full page refresh
- When run transitions to completed, it moves from Active to Completed tab
- Completed runs show [View Report] as primary row action
- Lecturers see only audit runs for their assigned modules

---

## Screen 38: Trigger Audit Dialog

**Route:** Modal overlay (no dedicated route)
**Purpose:** Select scope and agents for a new audit run. Accessible from multiple contexts.
**Roles:** SA, QA, Dean, HOD, PC

### Components
- Dialog — centred modal, 560px wide
- RadioGroup — scope selection
- Combobox — module/programme/department selector (contextual)
- Checkbox grid — agent selection (7 module agents + 1 programme agent)
- InfoCallout — run count preview
- Button (primary) — "Trigger Audits"

### Scope Options
- Single module with Module combobox selector
- All modules in programme with Programme combobox selector
- All modules in department (bulk) with Department combobox selector (SA, QA only)

### Agent Checkboxes
Module Folder Audit, Assessment Compliance, Moderation Compliance, Attendance Compliance, Evidence Verification, Outcome Alignment, Accreditation Readiness (all pre-checked), Programme Review (unchecked, disabled for single module scope).
[Select All] and [Clear All] links.

### Preview Line
"{n} agents x {m} modules = {n*m} audit runs will be created"

### API Endpoints (on submit — all return HTTP 202)
- POST /audits/modules/{id}/trigger
- POST /assessment-audits/modules/{id}/trigger
- POST /moderation-audits/modules/{id}/trigger
- POST /attendance-audits/modules/{id}/trigger
- POST /evidence-audits/modules/{id}/trigger
- POST /outcome-alignment-audits/modules/{id}/trigger
- POST /accreditation-readiness-audits/modules/{id}/trigger
- POST /programme-review-audits/programmes/{id}/trigger

### Acceptance Criteria
- Pre-filled module/agent when opened from a context
- "Programme Review" checkbox is disabled when scope is "Single module"
- Preview count updates when scope or agent selection changes
- All selected triggers fire in parallel
- Failed triggers show error toast per run without blocking successful ones
- Dialog is keyboard-navigable and focus-trapped

---

## Screen 39: Audit Progress

**Route:** /audits/[id]
**Purpose:** Live progress view for a single audit run. Polls until terminal state; shows results on completion.
**Roles:** All (if module access permitted)

### Components
- PageHeader — "{Agent Name} — {Module Code}", subtitle: "Run ID: {short UUID}"
- AuditProgressCard — animated state display
- Button — "View Report" (appears when status = completed)
- Button — "Trigger Again" (appears when status = completed or failed)
- ErrorCallout — shown when run_status = failed

### Progress Card States

Pending: "Queued — Waiting to start" with created_at timestamp.

Running: "Running — Analysing documents..." with agent type, module code, elapsed time, and animated spinner.

Completed: "Audit Complete" with compliance score, audit status, documents present/missing counts, findings count, and [View Full Report] button.

Failed: "Audit Failed" with error_message and [Trigger Again] button.

### Polling Logic
useAuditPolling hook: TanStack Query with refetchInterval: 3000.
Stop polling when run_status is completed or failed.
Show elapsed time counter (updated by local setInterval, not API).

### API Endpoints
- GET /audits/{id} — poll every 3 seconds until terminal

### Acceptance Criteria
- Page auto-updates without user interaction
- Elapsed time counter increments every second
- On completion: score, status badge, finding count appear; "View Report" button becomes primary
- On failure: error message displayed; "Trigger Again" offered
- Page is bookmarkable — refreshing resumes polling correctly
- aria-live="assertive" on status change for screen reader announcement

---

## Screen 40: Audit Report

**Route:** /audits/[id]/report
**Purpose:** Full structured audit report with compliance score, document checklist, and all findings. The primary output of the AQAA system.
**Roles:** All (scoped to module access)

### Components
- PageHeader — "{Agent Name} Report - {Module Code}", actions: [Export PDF] [Trigger Again]
- AuditReportHeader — score and metadata summary
- DocumentChecklistTable — present/missing checklist
- AuditFindingCard list — one card per finding
- FindingFilterBar — filter findings by severity and resolution status

### Report Header Section
Left panel: Compliance Score gauge (score/100, progress bar, AuditStatus badge).
Right panel: Agent, Module code and name, Programme, Institution, Triggered by, Started, Completed, Run ID.

### Document Checklist Section
Heading: "Document Checklist — {present} present, {missing} missing of {total} required"
Table: Category, Status Icon, Notes.
Present rows have green tint; missing rows have red tint.

### Findings Section
Heading: "Findings ({n})" with filter chips: All, Critical, High, Medium, Low, Resolved.

Each AuditFindingCard:
- Severity badge and finding title with [Resolve] button
- Type and document category metadata
- Full description text
- Full recommendation text
- Status (Open or Resolved with date and resolver name)

[Resolve] button opens ResolveFindingPanel (Screen 46).
Resolved findings show green header with resolution note and timestamp.

### Export PDF Action
window.print() on a print-optimised layout. Headers, navigation, and action buttons hidden in print CSS.

### API Endpoints
- GET /audits/{id}/report

### Acceptance Criteria
- Only accessible when run_status === completed; redirect to /audits/{id} if not completed
- All findings shown with correct severity ordering (Critical first)
- [Resolve] opens side panel without navigating away
- After resolving a finding, the card updates to resolved state without full reload
- PDF export produces a clean, branded print layout
- aria-label on each finding card for screen reader context

---

## Screen 41: Module Audit History

**Route:** /modules/[id]/audit-history
**Purpose:** Full history of all audit runs for a specific module across all agents and cycles.
**Roles:** All (scoped to module access)

### Components
- PageHeader — "{Module Code} — Audit History"
- DataTableToolbar — filter by agent, status, date range
- DataTable — all audit runs

### Table Columns
Agent, Status Badge, Score, Audit Status, Findings, Triggered By, Created, Completed, Actions.

### API Endpoints
- GET /audits/modules/{id}/history

---

## Screen 42: Programme Audit

**Route:** /programmes/[id]/audit
**Purpose:** Trigger and monitor Programme Review audits (programme-scoped agent).
**Roles:** SA, QA, Dean, HOD, PC

### Components
- PageHeader — "{Programme Code} — Programme Review Audit"
- LatestReviewCard — last Programme Review result
- ProgrammeReviewHistoryTable — all programme review runs
- Button (primary) — "Trigger New Programme Review"

### API Endpoints
- GET /programme-review-audits/programmes/{id}/latest
- GET /programme-review-audits/programmes/{id}/history
- POST /programme-review-audits/programmes/{id}/trigger

### Acceptance Criteria
- Trigger button fires POST and redirects to /programme-audits/{run_id} polling page
- History table shows all previous programme reviews

---

## Screen 43: Programme Audit Report

**Route:** /programme-audits/[id]/report
**Purpose:** Full structured Programme Review report aggregating compliance across all programme modules.
**Roles:** All (scoped to programme access)

Same layout as Screen 40 (Audit Report) but with programme-review-specific schema:
- Programme-level compliance score
- Per-module breakdown section (replacing document checklist)
- Programme-level findings

### API Endpoints
- GET /programme-review-audits/{id}

---

# PART 11 — FINDINGS MANAGEMENT

---

## Screen 44: Findings List

**Route:** /findings
**Purpose:** Centralised view of all audit findings. Filter, sort, and initiate resolution.
**Roles:** All (role-scoped; students read-only)

### Components
- PageHeader — "Findings", subtitle: "{n} open - {n} resolved (last 30 days)"
- Tabs — Open, In Progress, Resolved, All
- DataTableToolbar — search by title; filter by severity, agent, module, date
- DataTable — finding rows
- ResolveFindingPanel — slide-over panel (Screen 46)

### Table Columns

| Column | Type | Sortable | Filterable |
|--------|------|----------|-----------|
| Severity | badge with icon | Yes | Yes |
| Module | text and link | Yes | Yes |
| Finding Title | text | No | No |
| Type | badge | No | Yes |
| Agent | text | No | Yes |
| Days Open | number | Yes | No |
| Resolved By | text (resolved tab) | No | No |
| Resolved At | date (resolved tab) | Yes | No |
| Actions | button | No | No |

### Row Actions
- "View" to /findings/{id}
- "Resolve" opens ResolveFindingPanel (for open findings; PC+)
- "View Module" to /modules/{module_id}
- "View Report" to /audits/{audit_run_id}/report

### API Endpoints
- GET /findings (institution-scoped; module-scoped for Lecturers)

### Acceptance Criteria
- "Open" tab is the default
- Days Open column shows warning colour (amber for >7 days, red for >14 days)
- Students can see findings for their programme modules but cannot resolve
- Bulk resolve is QA Officer and above only

---

## Screen 45: Finding Detail

**Route:** /findings/[id]
**Purpose:** Full detail view of a single finding with resolution history.
**Roles:** All (scoped to module access)

### Components
- PageHeader — finding title and severity badge, actions: [Resolve Finding] (if open, PC+)
- Card (Finding Detail) — all finding properties
- Card (Resolution) — resolution note, resolver, timestamp (if resolved)
- Card (Context) — link to audit report and module

### Finding Detail Properties

| Field | Value |
|-------|-------|
| Severity | badge |
| Finding Type | badge |
| Document Category | badge (if applicable) |
| Description | full text |
| Recommendation | full text |
| Status | Open or Resolved badge |
| Raised At | formatted date |
| Audit Run | link to /audits/{id}/report |
| Module | link to /modules/{id} |
| File Involved | link to /files/{id} (if applicable) |

### API Endpoints
- GET /audits/{audit_run_id} (finding is nested in run)

---

## Screen 46: Resolve Finding Panel (Slide-Over)

**Route:** Slide-over panel — triggered from Screens 40, 44, 45
**Purpose:** Mark a finding as resolved with a required resolution note.
**Roles:** SA, QA, Dean, HOD, PC, Lec

### Components
- Sheet (ShadCN) — right-side slide-over, 520px wide
- SheetHeader — severity badge and finding title
- Card (Finding Summary) — description and recommendation (read-only)
- Textarea — resolution note (required)
- Button — upload related file (opens file browser, uploads to same module)
- Button (primary) — "Mark as Resolved"
- Button (secondary) — "Cancel"

### Fields

| Field | Label | Required | Constraints |
|-------|-------|----------|-------------|
| note | Resolution Note | Yes | 10-1000 chars; describe the remediation taken |

### Post-Resolution Behaviour
- Panel closes
- Finding status badge on the parent page updates to "Resolved" without page reload
- Success toast: "Finding marked as resolved"
- Prompt: "Would you like to trigger a new audit to verify improvement?" with [Run Audit] action

### API Endpoints
- POST /audits/{audit_run_id}/findings/{finding_id}/resolve — body: { note: "..." }

### Validation Rules
- note: required, minimum 10 characters
- Error shown inline below textarea with character count remaining

### Acceptance Criteria
- Panel slides in from the right, not centre of screen
- Finding detail (description and recommendation) visible in the panel for context
- Note field requires minimum 10 characters
- On resolve: parent list/report updates in place (no navigation)
- Focus returns to the trigger button when panel closes

---

# PART 12 — REPORTS AND ANALYTICS

---

## Screen 47: Compliance Report

**Route:** /reports/compliance
**Purpose:** Institution-wide compliance matrix with drill-down from institution to module level.
**Roles:** SA, QA, Dean, HOD, PC

### Components
- PageHeader — "Compliance Report", actions: [Export PDF] [Export XLSX]
- ReportFilters — Institution (SA only), Academic Year, Agent Type
- ComplianceMatrixDrilldown — collapsible tree component
- ComplianceHeatmapGrid — colour-coded grid (modules across agents)

### Compliance Matrix Drilldown
Tree structure: Institution, Faculties, Departments, Programmes, Modules.
Each node shows: name, avg compliance score, coloured score bar, expand/collapse chevron.
Leaf (module) nodes show: last score per agent, status badge, [View Report] link.

### Compliance Heatmap Grid
Rows: Modules. Columns: 8 Agents.
Cell: compliance score or dash (never run). Background: colour-coded by score range.
Hover tooltip: module name, agent name, score, last run date.

### API Endpoints
- GET /institutions
- GET /faculties
- GET /departments
- GET /programmes
- GET /modules
- GET /audits?institution_id={id}&limit=200

### Acceptance Criteria
- Drilldown tree is fully keyboard-accessible
- "Export XLSX" downloads a spreadsheet matching the matrix structure
- SA sees all institutions; QA sees only their institution

---

## Screen 48: Trend Analysis

**Route:** /reports/trends
**Purpose:** Multi-period compliance trend chart showing improvement or decline over time.
**Roles:** SA, QA, Dean

### Components
- PageHeader — "Compliance Trends"
- TrendFilters — scope (institution/faculty/module), date range, agent type
- ComplianceTrendChart — Recharts LineChart
- TrendSummaryTable — tabular version of chart data

### Chart Specification
- X-axis: time (monthly buckets)
- Y-axis: compliance score 0-100
- One line per selected scope entity
- Reference lines at 90 (compliant), 70 (needs attention), 50 (non-compliant)
- Tooltip: date, entity name, score

### API Endpoints
- GET /audits?institution_id={id}&run_status=completed&limit=500

---

## Screen 49: Evidence Coverage

**Route:** /reports/evidence
**Purpose:** Cross-institution analysis of which document categories are present or missing across modules.
**Roles:** SA, QA, Dean, HOD

### Components
- PageHeader — "Evidence Coverage Report"
- CoverageFilters — faculty, department, academic year
- EvidenceCoverageMatrix — rows: modules; columns: document categories
- MissingDocumentRanking — ranked list of most-missing categories

### Coverage Matrix
Cells: tick (green) = present, cross (red) = missing, dash = not categorised.
Export: [Export as XLSX].

### Missing Document Ranking
Horizontal bar chart. Each bar: document category, count of modules missing it.
Sorted descending by count.

### API Endpoints
- GET /files?institution_id={id}
- GET /modules?institution_id={id}

---

## Screen 50: Findings Summary

**Route:** /reports/findings
**Purpose:** Aggregated view of findings by severity, type, agent, and resolution status.
**Roles:** SA, QA, Dean, HOD

### Components
- PageHeader — "Findings Summary Report"
- FindingFilters — severity, agent, date range, resolution status
- FindingsBySeverityChart — donut chart
- FindingsByTypeChart — horizontal bar chart
- FindingsByAgentChart — horizontal bar chart
- FindingsTimelineChart — line chart (new findings per week)
- FindingsSummaryTable — tabular finding list

### API Endpoints
- GET /findings?institution_id={id} (role-scoped)

---

## Screen 51: Export Centre

**Route:** /reports/export
**Purpose:** Generate and download formal reports in PDF and XLSX formats.
**Roles:** SA, QA, Dean

### Report Types

| Report | Formats | Generation Method |
|--------|---------|------------------|
| Compliance Summary | PDF, XLSX | Client-side print layout and papaparse |
| Accreditation Readiness | PDF | Client-side print layout |
| Findings Register | XLSX | papaparse |
| Evidence Coverage Matrix | XLSX | papaparse |
| Audit History | XLSX, CSV | papaparse |
| Programme Compliance | PDF | Client-side print layout |
| Cycle Comparison | PDF, XLSX | Client-side and papaparse |

### Generation Flow
1. User clicks [Generate] on a report card
2. Scope/filter panel expands
3. User clicks [Download]
4. PDF: window.print() on print-layout page (new tab)
5. XLSX/CSV: generate client-side via papaparse then auto-download

### Acceptance Criteria
- All report types produce downloadable output
- PDF reports open in a new tab for browser print dialog
- XLSX/CSV files download automatically with descriptive filename including date
- Report generation shows a loading indicator while data is fetched

---

# PART 13 — ACCREDITATION

---

## Screen 52: Accreditation Readiness Dashboard

**Route:** /accreditation
**Purpose:** Institution-wide accreditation readiness overview. The primary screen for pre-submission review.
**Roles:** SA, QA, Dean, HOD, PC

### Components
- PageHeader — "Accreditation Readiness", subtitle: "Cycle: {academic_year}", actions: [Export Readiness Report]
- ReadinessGaugeCard — large radial gauge, overall score, risk level badge
- ReadinessByFacultyChart — horizontal bar chart
- UnresolvedCriticalFindingsWidget — top unresolved critical findings list

### Readiness Gauge Card
Centre value: overall readiness score (average of all Accreditation Readiness agent runs).
Ring colour: red (below 50), orange (50-69), amber (70-89), green (90+).
Sub-labels: Total Required Docs, Present, Missing, Unresolved Critical Findings.

### Readiness by Faculty Chart
Horizontal bar per faculty. Sorted ascending by score (most critical first).
Click bar navigates to /faculties/{id} compliance tab.

### Unresolved Critical Findings Widget
Top 10 unresolved critical severity findings.
Each row: module code, finding title, days open, [Resolve] action.

### API Endpoints
- GET /accreditation-readiness-audits/modules/{id}/latest (batched per module)
- GET /findings?institution_id={id}&severity=critical&is_resolved=false

### Acceptance Criteria
- Gauge reflects actual aggregated scores from Accreditation Readiness agent runs
- Faculty chart sorts by score ascending (worst first)
- "Export Readiness Report" generates a formal PDF for submission

---

## Screen 53: Cycle Comparison

**Route:** /accreditation/compare
**Purpose:** Side-by-side comparison of two accreditation cycles to show compliance improvement.
**Roles:** SA, QA

### Components
- PageHeader — "Cycle Comparison"
- CycleSelectorRow — two Select components: Cycle A and Cycle B
- CycleComparisonChart — grouped bar chart (one group per faculty, two bars each)
- ComplianceDeltaTable — table showing improvement/decline per module

### Cycle Selector
Academic year dropdowns.
Defaults: Cycle A = previous year, Cycle B = current year.

### Comparison Chart
X-axis: faculties. Y-axis: avg compliance score. Two bars per group: Cycle A (blue) and Cycle B (green).
Difference arrow: up arrow with + percentage (green) or down arrow with - percentage (red) above each group.

### Compliance Delta Table
Columns: Module Code, Module Name, Cycle A Score, Cycle B Score, Delta Change, Trend Arrow.

### API Endpoints
- GET /audits?academic_year={year_a}&institution_id={id}&run_status=completed
- GET /audits?academic_year={year_b}&institution_id={id}&run_status=completed

---

# PART 14 — NOTIFICATIONS

---

## Screen 54: Notification Centre

**Route:** /notifications
**Purpose:** Full list of all notifications for the current user with read/unread state management.
**Roles:** All

### Components
- PageHeader — "Notifications", actions: [Mark All Read]
- Tabs — All, Unread, Audit, Findings, Uploads
- NotificationList — scrollable list of NotificationItem rows

### Notification Item Anatomy
Unread dot indicator, event icon, title, time ago label, description (1 line truncated), action link.

### Notification Types and Icons
- Audit Complete — CheckCircle2 (green)
- Critical Finding — AlertOctagon (red)
- Finding Resolved — CheckCheck (green)
- File Uploaded — Upload (blue)
- File Quarantined — ShieldAlert (red)
- Audit Failed — XCircle (red)
- Compliance Threshold Breach — TrendingDown (orange)

### Actions
- Mark as read (on click)
- Contextual action link: [View Report], [Resolve], [View File]
- Swipe left to dismiss (mobile)

### API Endpoints
- GET /notifications (Phase 3 backend required)
- PATCH /notifications/{id}/read
- PATCH /notifications/read-all

### Acceptance Criteria
- Unread notifications have a blue left border accent
- Clicking a notification marks it read and navigates to the linked resource
- "Mark All Read" marks all visible notifications read
- Bell badge in topbar updates when new notifications arrive (polling every 30 seconds)
- aria-live="polite" region announces new notifications

---

## Screen 55: Notification Preferences

**Route:** /settings/notifications
**Purpose:** Configure which events trigger in-app and email notifications.
**Roles:** All

### Components
- PageHeader — "Notification Preferences" (within Settings layout)
- PreferencesTable — rows x channels toggle matrix

### Preferences Matrix

| Event | In-App | Email |
|-------|--------|-------|
| Audit completed | Toggle | Toggle |
| Critical finding raised | Toggle | Toggle |
| Finding resolved | Toggle | Toggle |
| Compliance threshold breach | Toggle | Toggle |
| File uploaded (my modules) | Toggle | Toggle |
| File quarantined | Toggle | Toggle |
| Audit failed | Toggle | Toggle |

Defaults: all In-App ON; Email ON for critical finding, audit complete, threshold breach.

### Acceptance Criteria
- Toggle changes save immediately (no submit button required)
- Saved state persists on page refresh

---

# PART 15 — USER MANAGEMENT

---

## Screen 56: Users List

**Route:** /users
**Purpose:** Manage all platform users. Invite, deactivate, and change roles.
**Roles:** SA

### Components
- PageHeader — "Users", subtitle: "{n} active - {n} pending invitations", actions: [+ Invite User] [Import CSV]
- DataTableToolbar — search by name/email; filter by role, institution, status
- DataTable — user rows

### Table Columns

| Column | Type | Sortable | Filterable |
|--------|------|----------|-----------|
| Name | text and avatar | Yes | No |
| Email | text | Yes | No |
| Role | badge | No | Yes |
| Institution | text | Yes | Yes |
| Status | badge (Active/Pending/Inactive) | No | Yes |
| Last Login | date | Yes | No |
| Joined | date | Yes | No |
| Actions | kebab | No | No |

### Row Actions
- "View Profile" to /users/{id}
- "Change Role" — inline role selector
- "Deactivate" — confirm dialog
- "Re-activate" — for inactive users
- "View Activity" to /users/{id}/activity
- "Resend Invitation" — for pending users

### API Endpoints
- GET /users (SA only — Phase 2 backend required)
- PATCH /users/{id}

---

## Screen 57: User Detail

**Route:** /users/[id]
**Purpose:** Full user profile view with role, institution, and activity statistics.
**Roles:** SA

### Components
- PageHeader — "{Full Name}", subtitle: role badge and institution, actions: [Edit User] [Deactivate]
- Card (Profile) — avatar, contact info, account stats
- Card (Permissions) — role and accessible modules (for Lecturers)
- RecentActivity — last 10 actions by this user

### Profile Card Fields
Email, Full Name, Role Badge, Institution, Status Badge, Last Login, Created At, Total Logins, Files Uploaded, Audit Runs Triggered.

### API Endpoints
- GET /users/{id} (Phase 2 backend required)
- GET /files?uploaded_by={id}&limit=5
- GET /audits?triggered_by={id}&limit=5

---

## Screen 58: Invite User

**Route:** /users/invite
**Purpose:** Send an email invitation to a new user with a specified role.
**Roles:** SA

### Fields

| Field | Type | Label | Required | Constraints |
|-------|------|-------|----------|-------------|
| email | email | Email Address | Yes | Valid email format; not already registered |
| full_name | text | Full Name | Yes | 2-255 chars |
| role | select | Role | Yes | Any role except system_admin |
| institution_id | select (searchable) | Institution | Yes | Valid institution UUID |

### Actions
Submit to POST /invitations (Phase 3 backend required) then show success: "Invitation sent to {email}."

### Validation Rules
- email: not already registered (server returns 409 if exists)
- role: system_admin excluded from dropdown options

### Acceptance Criteria
- On success: show confirmation screen with option to invite another user
- On 409: show inline error "This email address is already registered."

---

## Screen 59: User Activity Log

**Route:** /users/[id]/activity
**Purpose:** Audit trail of all actions performed by a specific user.
**Roles:** SA

### Table Columns
Timestamp, Action, Resource Type, Resource ID (copyable), IP Address, User Agent (truncated).

### Activity Types
Login, Logout, File Upload, Audit Trigger, Finding Resolved, Entity Created, Entity Updated, Entity Deleted.

### API Endpoints
- GET /users/{id}/activity (Phase 3 backend required)

---

# PART 16 — SETTINGS

---

## Screen 60: Profile Settings

**Route:** /settings/profile
**Purpose:** View and update personal profile information.
**Roles:** All

### Fields

| Field | Type | Label | Required | Editable |
|-------|------|-------|----------|---------|
| full_name | text | Full Name | Yes | Yes |
| email | email | Email Address | Yes | No (contact admin to change) |
| role | display | Role | — | No |
| institution | display | Institution | — | No |

### Actions
- [Save Changes] to PATCH /auth/me (Phase 3)
- Avatar upload to POST /users/me/avatar (Phase 3)

### Acceptance Criteria
- Email and role fields are visible but not editable (tooltip explains how to change)
- Save shows success toast "Profile updated"

---

## Screen 61: Password and Security

**Route:** /settings/security
**Purpose:** Change password and view active sessions.
**Roles:** All

### Fields

| Field | Type | Label | Required | Constraints |
|-------|------|-------|----------|-------------|
| current_password | password | Current Password | Yes | |
| new_password | password | New Password | Yes | Min 8 chars, 1 uppercase, 1 digit |
| confirm_password | password | Confirm New Password | Yes | Must match new_password |

### Password Strength Indicator
Live strength meter: Weak (red), Fair (amber), Strong (green).
Criteria checklist: 8+ characters, Uppercase letter, Digit.

### Actions
- [Change Password] to POST /auth/change-password (Phase 3 backend required)

### Validation Rules
- current_password: verified server-side; on failure: "Incorrect current password"
- new_password: min 8 chars, at least 1 uppercase, at least 1 digit
- confirm_password: must equal new_password (client-side check)

### Acceptance Criteria
- Success: all three fields cleared and success toast "Password changed successfully"
- Failed current password: inline error on current_password field

---

## Screen 62: System Settings

**Route:** /settings/system
**Purpose:** Configure platform-level application settings.
**Roles:** SA

### Sections

Application section:
- App Name (text, default: Academic Quality Assurance Agent)
- App Environment (select: development, staging, production)
- Default Academic Year (text, YYYY/YYYY format)
- Debug Mode (toggle, default: false)

CORS Origins section:
- Allowed Origins (tag input, comma-separated URL list)

Token Expiry section:
- Access Token Expiry in minutes (number, default: 60)
- Refresh Token Expiry in days (number, default: 7)

### Actions
- [Save Settings] to PATCH /settings/system (Phase 3 backend)
- [Test Connection] in health section to GET /health

### Acceptance Criteria
- Changes take effect after backend restart (note displayed)
- Debug toggle shows warning: "Enabling debug mode exposes stack traces in API responses"

---

## Screen 63: Email and SMTP Settings

**Route:** /settings/email
**Purpose:** Configure outgoing email for notifications and invitations.
**Roles:** SA

### Fields

| Field | Type | Label | Required |
|-------|------|-------|----------|
| smtp_host | text | SMTP Host | Yes |
| smtp_port | number | SMTP Port | Yes |
| smtp_user | text | SMTP Username | No |
| smtp_password | password | SMTP Password | No |
| smtp_tls | toggle | Use TLS | No |
| from_email | email | From Address | Yes |
| from_name | text | From Name | Yes |

### Actions
- [Save SMTP Settings]
- [Send Test Email] — sends a test email to the current admin's address

### Acceptance Criteria
- SMTP password field has show/hide toggle
- "Send Test Email" shows spinner during send and confirms delivery in toast
- If SMTP is not configured, notifications panel shows a warning

---

## Screen 64: Storage Settings

**Route:** /settings/storage
**Purpose:** Configure file storage backend and monitor usage.
**Roles:** SA

### Sections

Storage Backend section:
- Backend radio: Local, S3, or Azure Blob
- Local Path (text, shown if local selected, default: ./storage)
- S3 Bucket, Region, Access Key, Secret (shown if S3 selected)
- Azure Connection String (shown if Azure selected)

Upload Limits section:
- Max Upload Size in MB (number, default: 50)
- Virus Scanning (toggle, default: false)

Storage Usage Monitor section:
Total Used, Available, Files Count, By Category (mini bar chart).

### Actions
- [Save Storage Settings]
- [Test Connection] for S3/Azure — verifies credentials and bucket access

---

## Screen 65: Integrations

**Route:** /settings/integrations
**Purpose:** Configure external system connections (LMS, webhooks, SSO).
**Roles:** SA

### Integration Cards

LMS Integration (Phase 4):
- Provider: Moodle, Blackboard, or Canvas
- Base URL and API Key fields
- [Test Connection] button
- Status badge: Connected or Not Configured

Webhook Configuration (Phase 4):
- Endpoint URL field
- Secret key field
- Events checkboxes for each webhook event type
- [Save Webhook]

SSO/SAML (Phase 4):
- Provider: Azure AD, Okta, or Generic SAML
- Metadata URL or XML paste field
- SP Entity ID (read-only, auto-generated)
- ACS URL (read-only)

API Keys (Phase 3):
- Generate personal API key for external integrations
- List of existing API keys with last-used date and revoke button

### Acceptance Criteria
- Each integration section is independently configurable
- Unconfigured integrations show "Not Configured" badge with setup instructions
- Revoke API key requires confirmation dialog

---

# Appendix A — Cross-Cutting Acceptance Criteria

The following criteria apply to all 65 screens:

### Accessibility (WCAG 2.1 AA)
- All interactive elements reachable by keyboard (Tab, Enter, Space, Escape, Arrow keys)
- Focus ring visible on all interactive elements
- No outline: none without a visible focus alternative
- All images have alt text; decorative images have alt=""
- Form fields have visible label elements associated via for/id or wrapping
- Error messages use role="alert" or aria-live="polite"
- Status changes announce to screen readers via aria-live
- Colour is never the sole means of conveying information
- Text contrast meets 4.5:1 (body) and 3:1 (large text)
- html lang="en" on root layout

### Loading States
- All data-fetching surfaces show skeleton loaders while loading
- Skeleton dimensions match actual content dimensions (no layout shift)
- Submit buttons show spinner and are disabled during pending API calls

### Error States
- All API errors display a user-friendly message (not raw error objects)
- Network failures show "Unable to connect" toast with retry option
- 401 responses trigger token refresh; on refresh failure, redirect to /login
- 403 responses redirect to Screen 2 (Forbidden)
- 404 responses from API calls show Screen 3 (Not Found) content

### Empty States
- Every list page has an empty state with icon, heading, description, and CTA
- Charts display "No data available" message inside chart area when data is absent

### Responsive Design
- All screens functional at 375px, 768px, 1024px, and 1280px+ breakpoints
- No horizontal scroll on any breakpoint (excluding intentional overflow-x tables)
- Tables use horizontal scroll at mobile breakpoints with frozen first column
- Modals and panels are full-screen on mobile (below 640px)

### Performance
- First Contentful Paint under 1.5 seconds on 4G connection
- Skeleton loaders prevent cumulative layout shift (CLS under 0.1)
- Images use next/image with appropriate sizes attribute
- Fonts self-hosted via next/font (zero external requests)

### Security
- JWT tokens stored in httpOnly cookies only; never in localStorage or sessionStorage
- Token is injected server-side by Next.js API proxy routes
- No sensitive data (tokens, passwords) in URL parameters or browser history
- All forms protected against CSRF via SameSite=Strict cookie policy
- User-supplied content rendered as text, not HTML

---

# Appendix B — API Endpoint Quick Reference

| Domain | Endpoint Pattern | Methods |
|--------|-----------------|---------|
| Auth | /auth/token, /auth/login, /auth/refresh, /auth/me | POST, POST, POST, GET |
| Institutions | /institutions, /institutions/{id} | GET, POST, PATCH, DELETE |
| Faculties | /faculties, /faculties/{id} | GET, POST, PATCH, DELETE |
| Departments | /departments, /departments/{id} | GET, POST, PATCH, DELETE |
| Programmes | /programmes, /programmes/{id} | GET, POST, PATCH, DELETE |
| Modules | /modules, /modules/{id} | GET, POST, PATCH, DELETE |
| Files | /files/upload, /files, /files/{id}, /files/{id}/versions | POST, GET, GET, PATCH, DELETE |
| Audits (Folder) | /audits/modules/{id}/trigger, /audits/{id}, /audits/{id}/report | POST, GET, GET |
| Assessment Audits | /assessment-audits/modules/{id}/trigger, /{id} | POST, GET |
| Moderation Audits | /moderation-audits/modules/{id}/trigger, /{id} | POST, GET |
| Attendance Audits | /attendance-audits/modules/{id}/trigger, /{id} | POST, GET |
| Evidence Audits | /evidence-audits/modules/{id}/trigger, /{id} | POST, GET |
| Outcome Alignment | /outcome-alignment-audits/modules/{id}/trigger, /{id} | POST, GET |
| Accreditation | /accreditation-readiness-audits/modules/{id}/trigger, /{id} | POST, GET |
| Programme Review | /programme-review-audits/programmes/{id}/trigger, /{id} | POST, GET |
| Findings | /audits/{id}/findings/{fid}/resolve | POST |
| Health | /health | GET |

---

End of AQAA Master UI Specification — 65 screens documented.
Document maintained by: AQAA Frontend Architecture Team
Next review: After Phase 2 implementation complete
