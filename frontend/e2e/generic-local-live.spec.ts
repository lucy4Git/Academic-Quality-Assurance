import { expect, Page, test } from "@playwright/test";

const runId = Date.now().toString(36);
const password = "AQAA-Live-2026!";

async function registerAndOnboard(page: Page, persona: "QA Officer" | "Lecturer", email: string) {
  await page.goto("/register");
  await page.getByRole("radio", { name: persona === "QA Officer" ? "I review quality evidence and identify gaps" : "I prepare evidence and respond to findings" }).click();
  await page.getByLabel("Full name").fill(`Synthetic ${persona} ${runId}`);
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL(/\/login\?.*redirect=%2Fworkspace/);
  await expect(page.getByLabel("Email address")).toHaveValue(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/workspace$/, { timeout: 30_000 });
  const meResponse = await page.request.get("/api/proxy/auth/me");
  expect(meResponse.headers()["content-type"]).toContain("application/json");
  const profile = await meResponse.json();
  expect(profile.role).toBe("generic_user");
  expect(profile.persona).toBe(persona === "QA Officer" ? "quality_assurance_officer" : "lecturer");
}

async function send(page: Page, prompt: string, expected: RegExp) {
  await page.getByLabel("Ask AQAA").fill(prompt);
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(page.getByText(expected).last()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("button", { name: "Send message", exact: true })).toBeVisible();
}

test("QA Officer and Lecturer live journeys remain owner isolated", async ({ browser }) => {
  test.setTimeout(180_000);
  const qaEmail = `aqaa.qa.${runId}@example.com`;
  const lecturerEmail = `aqaa.lecturer.${runId}@example.com`;
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  const qaContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const qa = await qaContext.newPage();
  qa.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  qa.on("pageerror", (error) => {
    pageErrors.push(error.message);
    console.error(`[browser page error] ${error.message}`);
  });
  await registerAndOnboard(qa, "QA Officer", qaEmail);

  await expect(qa.getByRole("link", { name: "New conversation" })).toBeVisible({ timeout: 15_000 });
  const navLabels = await qa.getByRole("navigation", { name: "Primary navigation" }).getByRole("link").allTextContents();
  expect(navLabels).toEqual(["New conversation", "Search", "Library", "Files", "Saved outputs", "Recent"]);
  await expect(qa.getByLabel("Main navigation").getByText("Quality Assurance Officer", { exact: true })).toBeVisible();

  await qa.getByRole("link", { name: "Files" }).click();
  await expect(qa.getByRole("heading", { name: "Files" })).toBeVisible();
  const moduleName = `Evidence Practice ${runId}`;
  const evidenceName = `qa-evidence-${runId}.txt`;
  await qa.getByLabel("Module/course name").fill(moduleName);
  await qa.getByLabel("Code (optional)").fill(`QA-${runId}`);
  await qa.getByRole("button", { name: "Create workspace" }).click();
  await expect(qa.getByRole("heading", { name: "Upload evidence" })).toBeVisible();
  await qa.getByLabel("File", { exact: true }).setInputFiles({
    name: evidenceName,
    mimeType: "text/plain",
    buffer: Buffer.from("Module guide assessment paper outcomes rubric and moderation evidence for a synthetic QA test."),
  });
  await qa.getByLabel("Description (optional)").fill("Synthetic owner-scoped QA evidence");
  await qa.getByRole("button", { name: "Upload evidence" }).click();
  await expect(qa.getByText(evidenceName, { exact: true })).toBeVisible();
  await expect(qa.getByText(/· ready$/i)).toBeVisible();
  await qa.getByRole("button", { name: "Add to Library" }).click();
  const filesResponse = await qa.request.get("/api/proxy/files");
  expect(filesResponse.ok()).toBeTruthy();
  const qaFiles = await filesResponse.json() as Array<{ id: string; original_filename: string }>;
  const qaFileId = qaFiles.find((file) => file.original_filename === evidenceName)?.id;
  expect(qaFileId).toBeTruthy();

  await qa.getByRole("link", { name: "Library" }).click();
  await expect(qa.getByRole("heading", { name: "Library" })).toBeVisible();
  await expect(qa.getByText(evidenceName, { exact: true })).toBeVisible();

  await qa.getByRole("link", { name: "New conversation" }).click();
  await expect(qa.getByText("Suggested for Quality Assurance Officer")).toBeVisible();
  await send(qa, "Review my module folder and tell me which required documents are missing.", /Grounded QA finding/);
  await expect(qa.getByText(evidenceName, { exact: true })).toBeVisible();
  await send(qa, "For this review, assume I currently have a module guide and an assessment paper, but I do not have an assessment memorandum or an internal moderation report. What QA gaps should I address?", /Assessment Memorandum — MISSING/);
  await expect(qa.getByText(/Internal Moderation Report — MISSING/)).toBeVisible();
  await expect(qa.getByText(/based only on your statement/i)).toBeVisible();
  await send(qa, "Which of those gaps should I address first, and why?", /Address the Assessment Memorandum — MISSING first/);
  const qaConversationId = new URL(qa.url()).searchParams.get("session");
  expect(qaConversationId).toBeTruthy();
  await qa.getByRole("button", { name: "Save latest response" }).click();

  await qa.getByRole("link", { name: "Saved outputs" }).click();
  await expect(qa.getByRole("heading", { name: "Saved Outputs" })).toBeVisible();
  await expect(qa.getByRole("button", { name: "Which of those gaps should I address first, and why?", exact: true })).toBeVisible();
  const artifactResponse = await qa.request.get("/api/proxy/artifacts");
  const qaArtifacts = await artifactResponse.json() as Array<{ id: string }>;
  expect(qaArtifacts.length).toBeGreaterThan(0);
  const qaArtifactId = qaArtifacts[0].id;

  await qa.getByRole("link", { name: "Search" }).click();
  await qa.getByPlaceholder("Search your AQAA workspace").fill(evidenceName);
  await qa.getByRole("button", { name: "Search" }).click();
  await expect(qa.getByText(evidenceName, { exact: true })).toBeVisible();
  await qa.getByRole("link", { name: "Recent" }).click();
  await expect(qa).toHaveURL(/\/recent$/);
  await expect(qa.getByText(/Review my module folder/)).toBeVisible();
  await qa.reload();
  await expect(qa.getByText(/Review my module folder/)).toBeVisible({ timeout: 10_000 });
  expect(consoleErrors.filter((message) => !message.includes("favicon"))).toEqual([]);
  await qa.getByTitle("Sign out").click();
  await expect(qa).toHaveURL(new RegExp("/login"));
  await qa.goto("/login");
  await expect(qa.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  await qa.getByLabel("Email address").fill(qaEmail);
  await qa.getByLabel("Password", { exact: true }).fill(password);
  await qa.getByRole("button", { name: /sign in/i }).click();
  await expect(qa).toHaveURL(new RegExp("/workspace"));
  await qa.getByRole("link", { name: "Recent" }).click();
  await expect(qa.getByText(/Review my module folder/)).toBeVisible({ timeout: 10_000 });
  // Logout intentionally races the authenticated layout's final /auth/me
  // request, which can emit a transient 401/RSC fallback in Next dev mode.
  consoleErrors.length = 0;

  const lecturerContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const lecturer = await lecturerContext.newPage();
  await registerAndOnboard(lecturer, "Lecturer", lecturerEmail);
  await expect(lecturer.getByText("Suggested for Lecturer")).toBeVisible();
  await expect(lecturer.getByRole("button", { name: /Find missing documents/ })).toBeVisible();
  await send(lecturer, "Review my module folder and tell me which required documents are missing.", /UNABLE TO DETERMINE/);

  const deny = async (path: string) => {
    const response = await lecturer.request.get(path);
    expect([403, 404]).toContain(response.status());
  };
  await deny(`/api/proxy/files/${qaFileId}`);
  await deny(`/api/proxy/files/${qaFileId}/download`);
  await deny(`/api/proxy/artifacts/${qaArtifactId}`);
  await deny(`/api/proxy/ai-assistant/sessions/${qaConversationId}`);
  const lecturerFiles = await lecturer.request.get("/api/proxy/files");
  expect(JSON.stringify(await lecturerFiles.json())).not.toContain(evidenceName);
  const lecturerSearch = await lecturer.request.get(`/api/proxy/search?q=${encodeURIComponent(evidenceName)}`);
  expect(await lecturerSearch.json()).toEqual([]);
  const attachAttempt = await lecturer.request.post("/api/proxy/ai-assistant/ask-stream", {
    data: { question: "Review the attached evidence", attached_file_ids: [qaFileId] },
  });
  expect([403, 404]).toContain(attachAttempt.status());

  for (const viewport of [{ width: 768, height: 900 }, { width: 390, height: 844 }]) {
    await qa.setViewportSize(viewport);
    for (const route of ["/workspace", "/files", "/library", "/search", "/saved", "/recent"]) {
      await qa.goto(route);
      const overflow = await qa.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
      expect(overflow, `${route} overflows at ${viewport.width}px`).toBeFalsy();
    }
  }

  expect(pageErrors).toEqual([]);
  expect(consoleErrors.filter((message) => !message.includes("favicon"))).toEqual([]);
  await lecturerContext.close();
  await qaContext.close();
});
