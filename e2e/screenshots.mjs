// Regenerates the screenshots in docs/screenshots/ that the README and docs use, from a freshly seeded stack.
// Usage (from e2e/, stack on :8080 with a fresh database): node screenshots.mjs [baseURL]
// PW_CHROMIUM points at a preinstalled Chromium, as for the browser tests.
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";

const BASE = (process.argv[2] ?? process.env.BASE_URL ?? "http://localhost:8080").replace(/\/$/, "");
const PASSWORD = process.env.DEMO_PASSWORD ?? "claimsense-demo";
const OUT = fileURLToPath(new URL("../docs/screenshots/", import.meta.url));
const DATA = fileURLToPath(new URL("../data/", import.meta.url));
const WIDTH = 1440, HEIGHT = 1000;

const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));

// Full-page shots grow the viewport to the page height, so the fixed sidebar spans the whole image.
async function shot(name, { full = true } = {}) {
  await page.waitForLoadState("networkidle");
  if (full) {
    const h = await page.evaluate(() => document.documentElement.scrollHeight);
    await page.setViewportSize({ width: WIDTH, height: Math.max(HEIGHT, h) });
  }
  await page.screenshot({ path: `${OUT}${name}.png` });
  await page.setViewportSize({ width: WIDTH, height: HEIGHT });
  console.log(`  ${name}.png`);
}

async function signIn(role) {
  await page.goto(`${BASE}/`);
  await page.evaluate(() => localStorage.clear());
  await page.goto(`${BASE}/`);
  await page.getByRole("button", { name: new RegExp(`${role} ·`) }).click();
  await page.getByLabel(/password/i).fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByText("AI recommendations").waitFor();
}

// Setup steps go straight to the API with the signed-in user's token.
async function api(method, path, body) {
  const r = await page.evaluate(async ([method, url, body]) => {
    const res = await fetch(url, { method, headers: { "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("claimsense.token")}` }, body: body ? JSON.stringify(body) : undefined });
    return { status: res.status, text: await res.text() };
  }, [method, `${BASE}/api/v1${path}`, body]);
  if (r.status >= 400) throw new Error(`${method} ${path}: HTTP ${r.status} ${r.text}`);
}

async function claim(number, tab, name, opts) {
  await page.goto(`${BASE}/claims/${number}#${tab}`);
  await page.getByRole("tab", { selected: true }).waitFor();
  await shot(name, opts);
}

console.log(`Screenshots from ${BASE}`);
await signIn("Adjuster");
await page.goto(`${BASE}/claims/new`);
await page.locator("select").first().selectOption("CS-HLT-23-000089");
await page.locator("textarea").fill("Kidney stone treatment, uploaded through the browser.");
await page.locator("input[type=file]").setInputFiles(["claim_form.txt", "hospital_bill.txt", "discharge_summary.txt"]
  .map((f) => `${DATA}claims/demo_upload/${f}`));
await page.getByRole("button", { name: "Create, upload and analyse" }).click();
await page.getByText("AI recommendation · requires human review").waitFor({ timeout: 30_000 });
await shot("02-claim-analysis");
await claim("CLM-H-1002", "overview", "04-claim-rejected-waiting-period");
await claim("CLM-H-1003", "risk", "05-claim-high-risk");
await claim("CLM-M-2001", "adjudication", "06-motor-depreciation");
await page.goto(`${BASE}/assistant`);
await page.getByRole("button", { name: "Is cataract surgery covered in the first year?" }).click();
await page.locator(".answer, .card", { hasText: "§" }).first().waitFor();
await shot("07-policy-assistant");
await page.goto(`${BASE}/reviews`);
await page.getByText("Open tasks").waitFor();
await shot("08-review-queue");

await signIn("Supervisor");
await api("POST", "/claims/CLM-H-1002/review", { action: "REJECT",
  notes: "Cataract surgery about six months into cover; the 24-month specified-disease waiting period (3.3) applies." });
await page.goto(`${BASE}/claims/CLM-H-1002#review`);
await page.getByRole("button", { name: "Generate letter" }).click();
await page.locator(".letter").waitFor();
await shot("12-rejection-letter");
await page.goto(`${BASE}/evaluation`);
await page.getByText("Checks passed").waitFor();
await shot("13-evaluation");
await page.goto(`${BASE}/policies`);
await page.locator("input[type=file]").nth(0).setInputFiles(`${DATA}policies/ingest_demo/HLT-SHIELD_2026.1.pdf`);
await page.locator("input[type=file]").nth(1).setInputFiles(`${DATA}policies/ingest_demo/HLT-SHIELD_2026.1.terms.json`);
await page.getByRole("button", { name: "Ingest and index" }).click();
await page.locator(".ok-text").waitFor({ timeout: 30_000 });
await shot("15-policy-pdf-ingestion");
await claim("CLM-H-1001", "evidence", "16-claim-evidence");
await page.goto(`${BASE}/datasets`);
await page.waitForLoadState("networkidle");
await shot("17-data-provenance");
await api("POST", "/claims/CLM-H-1001/facts", { name: "hospital",
  value: "Lakeview Multispeciality Hospital and Research Centre (fictional)",
  reason: "Discharge summary letterhead gives the full name" });
await claim("CLM-H-1001", "documents", "18-fact-correction");
await claim("CLM-P-3001", "adjudication", "20-property-claim-adjudication", { full: false });
await claim("CLM-T-4002", "adjudication", "21-travel-claim-adjudication", { full: false });
await page.goto(`${BASE}/claims`);
await page.locator("tbody tr").first().waitFor();
await shot("22-claims-all-lines");
await page.goto(`${BASE}/`);
await page.getByText("Lines of business").waitFor();
await shot("23-dashboard-interactive");
await page.locator("table.lines").getByRole("link", { name: "Travel" }).click();
await page.getByText(/Showing \d+ of \d+ claims where/).waitFor();
await shot("24-claims-filtered-travel", { full: false });
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(`${BASE}/`);
await page.getByText("Lines of business").waitFor();
await page.waitForLoadState("networkidle");
await page.screenshot({ path: `${OUT}19-mobile-dashboard.png` });
console.log("  19-mobile-dashboard.png");

await browser.close();
if (errors.length) { console.error("Browser errors:\n" + errors.join("\n")); process.exit(1); }
console.log("Done, no browser errors.");
