// The Claim Sense golden path and the reviewer screens, driven through the real UI and API.
// Written for a freshly seeded stack; every value asserted here is produced by the running system.
import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const DEMO = fileURLToPath(new URL("../../data/claims/demo_upload/", import.meta.url));
const PASSWORD = process.env.DEMO_PASSWORD ?? "claimsense-demo";

let errors = [];
test.beforeEach(async ({ page }) => {
  errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(String(e)));
});
test.afterEach(() => expect(errors, "browser console errors").toEqual([]));

async function signIn(page, role) {
  await page.goto("/");
  await page.getByRole("button", { name: new RegExp(`${role} ·`) }).click();
  await page.getByLabel(/password/i).fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("AI recommendations")).toBeVisible();
}

test.describe.configure({ mode: "serial" });

test("golden path: create, upload, analyse, approve and write the letter", async ({ page }) => {
  await signIn(page, "Adjuster");
  await page.goto("/claims/new");
  await page.locator("select").first().selectOption("CS-HLT-23-000089");
  await page.locator("textarea").fill("Kidney stone treatment, uploaded through the browser test.");
  await page.locator("input[type=file]").setInputFiles(["claim_form.txt", "hospital_bill.txt", "discharge_summary.txt"].map((f) => DEMO + f));
  await page.getByRole("button", { name: "Create, upload and analyse" }).click();
  await expect(page.getByText("AI recommendation · requires human review")).toBeVisible({ timeout: 30_000 });
  await expect(page.locator(".amounts .pay strong")).toHaveText("₹64,080");
  await expect(page.locator(".recommendation .badge").first()).toHaveText("Partial approval");
  for (const agent of ["Intake Agent", "Policy Retrieval Agent", "Coverage Agent", "Adjudication Tool", "Risk/Fraud Agent", "Evidence Agent"]) {
    await expect(page.locator("ol.pipeline").getByText(agent, { exact: true })).toBeVisible();
  }
  await page.getByRole("tab", { name: /^Policy & evidence/ }).click();
  await expect(page.getByRole("heading", { name: "Policy in force" })).toBeVisible();
  await page.getByRole("tab", { name: /^Review/ }).click();
  await page.locator("textarea").fill("Verified the bill against the discharge summary.");
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByText("Reviewer Adjuster A. Rao")).toBeVisible();
  await expect(page.locator("h1 .badge")).toHaveText("Approved");
  await page.getByRole("button", { name: "Generate letter" }).click();
  await expect(page.locator(".letter")).toContainText("INR 64,080.00");
  await page.getByRole("tab", { name: /^Audit/ }).click();
  for (const event of ["Policy selected", "Coverage analyzed", "Adjudication calculated", "Risk scored", "Human decision"]) {
    await expect(page.getByText(event, { exact: true }).first()).toBeVisible();
  }
});

test("an adjuster cannot approve above their limit", async ({ page }) => {
  await signIn(page, "Adjuster");
  await page.goto("/claims/CLM-H-1003#review");
  await expect(page.getByText("above your approval limit")).toBeVisible();
  await expect(page.getByRole("button", { name: "Approve", exact: true })).toBeDisabled();
});

test("rejection cites the waiting-period clause", async ({ page }) => {
  await signIn(page, "Auditor");
  await page.goto("/claims/CLM-H-1002#coverage");
  await expect(page.getByText("Specified disease waiting").first()).toBeVisible();
  await expect(page.getByText("§3.3").first()).toBeVisible();
});

test("assistant answers with a citation and refuses without evidence", async ({ page }) => {
  await signIn(page, "Auditor");
  await page.goto("/assistant");
  await page.getByRole("button", { name: "Is drunk driving covered?" }).click();
  await expect(page.getByText("Citations")).toBeVisible();
  await page.locator(".ask input").fill("What is the capital of France?");
  await page.getByRole("button", { name: "Ask" }).click();
  await expect(page.getByText("No sufficient evidence")).toBeVisible();
});

test("evaluation scorecard passes every check", async ({ page }) => {
  await signIn(page, "Auditor");
  await page.goto("/evaluation");
  const passed = page.locator(".kpi", { hasText: "Checks passed" }).locator("strong");
  await expect(passed).toHaveText(/^(\d+) \/ \1$/);
});

test("review tasks can be taken and released", async ({ page }) => {
  await signIn(page, "Adjuster");
  await page.goto("/reviews");
  const row = page.locator("tbody tr").filter({ has: page.getByRole("button", { name: "Take" }) }).first();
  const claim = await row.locator("a").first().innerText();
  await row.getByRole("button", { name: "Take" }).click();
  const mine = page.locator("tbody tr", { hasText: claim });
  await expect(mine.getByText("Adjuster A. Rao")).toBeVisible();
  await page.getByRole("button", { name: /Assigned to me/ }).click();
  await expect(page.locator("tbody tr", { hasText: claim })).toBeVisible();
  await page.locator("tbody tr", { hasText: claim }).getByRole("button", { name: "Release" }).click();
  await expect(page.locator("tbody tr", { hasText: claim })).toHaveCount(0);
});

test("a reviewer corrects an extracted fact and re-runs the analysis", async ({ page }) => {
  await signIn(page, "Supervisor");
  await page.goto("/claims/CLM-H-1001#documents");
  const row = page.locator("tr", { has: page.locator("td", { hasText: /^Hospital$/ }) });
  await row.getByRole("button", { name: "Correct" }).click();
  await page.getByLabel("New Hospital").fill("Lakeview Multispeciality Hospital and Research Centre (fictional)");
  await expect(page.getByRole("button", { name: "Save correction" })).toBeDisabled();
  await page.getByLabel("Reason for correction").fill("Discharge summary letterhead gives the full name");
  await page.getByRole("button", { name: "Save correction" }).click();
  await expect(page.getByText(/Corrected since the last analysis/)).toBeVisible();
  await page.getByRole("button", { name: "Re-run analysis" }).click();
  await expect(page.getByText(/Corrected since the last analysis/)).toHaveCount(0, { timeout: 30_000 });
  await expect(row.getByText("Corrected", { exact: true })).toBeVisible();
});

test("data provenance: registry verified and every RAG chunk traced", async ({ page }) => {
  await signIn(page, "Auditor");
  await page.goto("/datasets");
  const kpi = (label) => page.locator(".kpi", { hasText: label }).locator("strong");
  await expect(kpi("Provenance problems")).toHaveText("0");
  await expect(kpi("Chunks rejected")).toHaveText("0");
  await expect(kpi("Checksums verified")).toHaveText(/^(\d+) \/ \1$/);
});

test("dashboard shows the review rates", async ({ page }) => {
  await signIn(page, "Supervisor");
  await expect(page.locator(".kpi", { hasText: "Override rate" })).toBeVisible();
  await expect(page.locator(".kpi", { hasText: "Escalation rate" })).toBeVisible();
});

test("dashboard filters and tiles drill down to the matching claims", async ({ page }) => {
  await signIn(page, "Supervisor");
  await page.getByRole("group", { name: "Line of business" }).getByRole("button", { name: "Motor" }).click();
  await expect(page).toHaveURL(/line=motor/);
  await page.locator(".kpi", { hasText: "High risk" }).click();
  await expect(page).toHaveURL(/\/claims\?.*claim_type=motor.*risk=HIGH/);
  const rows = page.locator("table.clickable tbody tr");
  await expect(rows.first()).toBeVisible();
  for (const row of await rows.all()) {
    await expect(row.locator("td").nth(1)).toHaveText("motor");
    await expect(row).toContainText("High");
  }
  await page.getByRole("button", { name: "Clear all filters" }).click();
  await expect(page.locator(".tag.removable")).toHaveCount(0);
  await page.goto("/guide");
  await page.getByRole("link", { name: "Open CLM-H-1001" }).click();
  await expect(page).toHaveURL(/\/claims\/CLM-H-1001$/);
});

test("phone layout: navigation behind a menu, no sideways scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page, "Adjuster");
  await expect(page.locator("#main-nav")).toBeHidden();
  await page.getByRole("button", { name: "Menu" }).click();
  await page.getByRole("link", { name: "Review queue" }).click();
  await expect(page.getByText("Open tasks")).toBeVisible();
  await expect(page.locator("#main-nav")).toBeHidden();
  for (const path of ["/", "/claims", "/claims/CLM-H-1001", "/reviews", "/guide"]) {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const [scroll, client] = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
    expect(scroll, `${path} scrolls sideways`).toBeLessThanOrEqual(client);
  }
});
