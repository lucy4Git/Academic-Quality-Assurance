import { createHash } from "node:crypto";
import { expect, Page, test } from "@playwright/test";

const password = "AQAA-Upload-2026!";
const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64");
const jpeg = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0, 0x10, 0x4a, 0x46, 0x49, 0x46, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0xff, 0xd9]);
const text = Buffer.from("Synthetic owner-scoped QA evidence.\n");

function makePdf(): Buffer {
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
    "<< /Length 207 >>\nstream\nBT /F1 12 Tf 72 720 Td (Awarded to Synthetic Holder) Tj 0 -18 Td (Bachelor of Quality Assurance) Tj 0 -18 Td (AQAA Test University) Tj 0 -18 Td (Award date: 2026-09-09) Tj 0 -18 Td (Credential number: SYN-2026-001) Tj ET\nendstream",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];
  let value = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(Buffer.byteLength(value, "latin1"));
    value += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xref = Buffer.byteLength(value, "latin1");
  value += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  value += offsets.slice(1).map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`).join("");
  value += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(value, "latin1");
}
const pdf = makePdf();
const digest = (buffer: Buffer) => createHash("sha256").update(buffer).digest("hex");

async function register(page: Page, label: string) {
  const id = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
  const email = `aqaa.upload.${label}.${id}@example.com`;
  await page.goto("/register");
  await page.getByRole("radio", { name: "I review quality evidence and identify gaps" }).click();
  await page.getByLabel("Full name").fill(`Upload ${label} ${id}`);
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password").fill(password);
  const [created] = await Promise.all([
    page.waitForResponse((response) => response.url().includes("/api/auth/register"), { timeout: 120_000 }),
    page.getByRole("button", { name: "Create Account" }).click(),
  ]);
  expect(created.status()).toBe(201);
  await expect(page).toHaveURL(/redirect=%2Fworkspace/);
  await expect(page.getByLabel("Email address")).toHaveValue(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  const [login] = await Promise.all([
    page.waitForResponse((response) => response.url().includes("/api/auth/login"), { timeout: 120_000 }),
    page.getByRole("button", { name: /sign in/i }).click(),
  ]);
  expect(login.status()).toBe(200);
  await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByRole("button", { name: "Attach files from this device" })).toBeEnabled({ timeout: 30_000 });
}

async function upload(page: Page, workspace: string, name: string, mimeType: string, buffer: Buffer) {
  const response = await page.request.post("/api/proxy/files/upload", { multipart: {
    file: { name, mimeType, buffer }, workspace_module_id: workspace,
    category: "course_outline", description: "Synthetic integrity fixture.", is_library_item: "false",
  } });
  expect(response.status(), await response.text()).toBe(201);
  return response.json() as Promise<{ id: string; owner_user_id: string; upload_state: string }>;
}

test("proxy preserves bytes, validation, authentication, and ownership", async ({ browser, page }) => {
  test.setTimeout(420_000);
  await register(page, "owner-a");
  const workspaces = await (await page.request.get("/api/proxy/personal-workspaces")).json() as Array<{ id: string }>;
  expect(workspaces).toHaveLength(1);
  const fixtures = [
    ["certificate.png", "image/png", png], ["qa_evidence.jpg", "image/jpeg", jpeg],
    ["sample certificate.pdf", "application/pdf", pdf], ["qa-evidence.txt", "text/plain", text],
  ] as const;
  const ids: string[] = [];
  for (const [name, mimeType, buffer] of fixtures) {
    const record = await upload(page, workspaces[0].id, name, mimeType, buffer);
    expect(record.upload_state).toBe("ready");
    const download = await page.request.get(`/api/proxy/files/${record.id}/download`);
    expect(download.status(), `${name} download status`).toBe(200);
    expect(digest(Buffer.from(await download.body()))).toBe(digest(buffer));
    ids.push(record.id);
  }
  expect((await upload(page, workspaces[0].id, "evidence-δ.txt", "text/plain", text)).upload_state).toBe("ready");
  const unsupported = await page.request.post("/api/proxy/files/upload", { multipart: {
    file: { name: "unsafe.exe", mimeType: "application/octet-stream", buffer: Buffer.from("MZ") },
    workspace_module_id: workspaces[0].id, category: "course_outline",
  } });
  expect(unsupported.status()).toBe(422);
  const malformed = await page.request.fetch("/api/proxy/files/upload", {
    method: "POST", headers: { "Content-Type": "multipart/form-data; boundary=broken" }, data: "--broken\r\ninvalid",
  });
  expect([400, 422]).toContain(malformed.status());
  const anonymous = await browser.newContext();
  const denied = await anonymous.request.post("/api/proxy/files/upload", { multipart: {
    file: { name: "certificate.png", mimeType: "image/png", buffer: png },
  } });
  expect([401, 403]).toContain(denied.status());
  await anonymous.close();
  const other = await browser.newContext();
  const otherPage = await other.newPage();
  await register(otherPage, "owner-b");
  expect((await otherPage.request.get(`/api/proxy/files/${ids[0]}`)).status()).toBe(404);
  expect((await otherPage.request.get(`/api/proxy/files/${ids[0]}/download`)).status()).toBe(404);
  await other.close();
});

test("composer supports direct upload, removal, drop, and credential review", async ({ page }) => {
  test.setTimeout(300_000);
  await register(page, "composer");
  const input = page.locator('input[type="file"]');
  await input.setInputFiles({ name: "certificate.png", mimeType: "image/png", buffer: png });
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Remove certificate.png" }).first().click();
  await expect(page.getByText("certificate.png", { exact: true })).toBeHidden();
  await input.setInputFiles({ name: "certificate.png", mimeType: "image/png", buffer: png });
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Review selected credential" }).click();
  await expect(page.getByRole("heading", { name: "Credential review" })).toBeVisible();
  await expect(page.getByText(/UNABLE TO DETERMINE/).first()).toBeVisible();
  await expect(page.getByText(/No issuer registry or external verification provider is configured/)).toBeVisible();
  await page.getByRole("button", { name: "Remove certificate.png" }).first().click();
  await input.setInputFiles({ name: "sample certificate.pdf", mimeType: "application/pdf", buffer: pdf });
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Review selected credential" }).click();
  await expect(page.getByText(/Synthetic Holder/).first()).toBeVisible();
  await expect(page.getByText(/Bachelor of Quality Assurance/).first()).toBeVisible();
  await expect(page.getByText(/not_verified/)).toBeVisible();
  const [saved] = await Promise.all([
    page.waitForResponse((response) => response.url().includes("/api/proxy/artifacts") && response.request().method() === "POST"),
    page.getByRole("button", { name: "Save latest response" }).click(),
  ]);
  expect(saved.status()).toBe(201);
  await page.getByRole("link", { name: "Saved outputs" }).click();
  await expect(page.getByText("Review this academic credential.", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "New conversation" }).click();
  await expect(page.getByRole("button", { name: "Attach files from this device" })).toBeEnabled({ timeout: 30_000 });
  await page.getByLabel("Ask AQAA").locator("xpath=ancestor::form").evaluate((form, bytes) => {
    const value = new DataTransfer();
    value.items.add(new File([new Uint8Array(bytes)], "drag-certificate.png", { type: "image/png" }));
    form.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, dataTransfer: value }));
  }, Array.from(png));
  await expect(page.getByText("drag-certificate.png", { exact: true })).toBeVisible();
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
});
