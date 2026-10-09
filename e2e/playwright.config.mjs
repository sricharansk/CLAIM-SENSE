import { defineConfig } from "@playwright/test";

// Run against a freshly seeded stack: docker compose up -d && npm test. A second run on the same database files the
// golden claim again, and the system rightly flags it as a duplicate, so reset with docker compose down -v first.
// BASE_URL overrides the target;
// PW_CHROMIUM points at a preinstalled Chromium instead of the one `npx playwright install` downloads.
export default defineConfig({
  testDir: "tests",
  timeout: 60_000,
  workers: 1,
  fullyParallel: false,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "report" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:8080",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {},
  },
});
