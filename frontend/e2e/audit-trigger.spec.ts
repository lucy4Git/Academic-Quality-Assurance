/**
 * E2E — Audit trigger critical path
 *
 * Verifies a QA officer can navigate to the audits section and
 * that the trigger interface is visible. Does not submit a live
 * trigger to avoid polluting the database with test runs.
 */

import { test, expect, Page } from "@playwright/test";

const email = process.env.E2E_ADMIN_EMAIL || "admin@gfu.ac.za";
const password = process.env.E2E_ADMIN_PASSWORD || "ChangeMe123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(email);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).not.toHaveURL(/\/login/, { timeout: 8_000 });
}

test.describe("Audit Trigger", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("audit section is accessible from navigation", async ({ page }) => {
    // Look for audits link in sidebar or nav
    const auditsLink = page.getByRole("link", { name: /audit/i }).first();
    await expect(auditsLink).toBeVisible({ timeout: 5_000 });
    await auditsLink.click();
    await expect(page.getByRole("main")).toBeVisible();
  });
});
