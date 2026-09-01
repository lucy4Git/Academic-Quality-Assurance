import { expect, test } from "@playwright/test";

const runId = Date.now().toString(36);
const password = "AQAA-Polish-2026!";

test("atomic signup, direct attachment, credential report, profile and recent actions", async ({ page }) => {
  test.setTimeout(120_000);
  const email = `aqaa.polish.${runId}@example.com`;
  await page.goto("/register");
  await page.getByRole("radio", { name: "I review quality evidence and identify gaps" }).click();
  await page.getByLabel("Full name").fill(`Synthetic Polish ${runId}`);
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL(/redirect=%2Fworkspace/);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByText("Suggested for Quality Assurance Officer")).toBeVisible();

  const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64");
  await page.locator('input[type="file"]').setInputFiles({ name: `credential-${runId}.png`, mimeType: "image/png", buffer: png });
  await expect(page.getByText("Ready", { exact: true })).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "Review selected credential" }).click();
  await expect(page.getByRole("heading", { name: "Credential review" })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/No issuer registry or external verification provider is configured/)).toBeVisible();
  await expect(page.getByText(/UNABLE TO DETERMINE/).first()).toBeVisible();

  await page.getByRole("button", { name: "Profile menu" }).click();
  await expect(page.getByRole("menuitem", { name: "Personalization / Work focus" })).toBeVisible();
  await expect(page.getByRole("menuitem", { name: "Help" })).toBeVisible();
  await page.keyboard.press("Escape");

  const session = await page.request.post("/api/proxy/ai-assistant/sessions", { data: { title: `Polish conversation ${runId}`, mode: "qa_assistant" } });
  expect(session.ok()).toBeTruthy();
  await page.goto("/recent");
  await expect(page.getByText(`Polish conversation ${runId}`)).toBeVisible();
  await page.getByRole("button", { name: `Actions for Polish conversation ${runId}` }).click();
  await expect(page.getByRole("menuitem", { name: "Rename" })).toBeVisible();
  await expect(page.getByRole("menuitem", { name: "Pin" })).toBeVisible();
  await expect(page.getByRole("menuitem", { name: "Archive" })).toBeVisible();
  await expect(page.getByRole("menuitem", { name: "Delete" })).toBeVisible();
});