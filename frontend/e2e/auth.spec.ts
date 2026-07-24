/**
 * E2E — Authentication critical path
 *
 * E0-OD-008: Synthetic test credentials only. No real institutional
 * or personal data may be used in E2E tests. CI credentials are
 * supplied via GitHub Actions secrets.
 *
 * Tests use the seeded QA officer account (password: ChangeMe123!)
 * or E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD environment variables.
 */

import { test, expect } from "@playwright/test";

const email = process.env.E2E_ADMIN_EMAIL || "admin@gfu.ac.za";
const password = process.env.E2E_ADMIN_PASSWORD || "ChangeMe123!";

test.describe("Authentication", () => {
  test("login page renders", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
  });

  test("invalid credentials shows error", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("bad@example.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/invalid|incorrect|unauthorized/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("valid credentials redirect to dashboard", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /sign in/i }).click();

    // Should leave /login after successful auth
    await expect(page).not.toHaveURL(/\/login/, { timeout: 8_000 });
    // Dashboard or home route should be visible
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("unauthenticated navigation redirects to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/, { timeout: 5_000 });
  });
});
