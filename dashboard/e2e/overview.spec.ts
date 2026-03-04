import { test, expect } from "@playwright/test";

test.describe("Overview Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("renders heading and subtitle", async ({ page }) => {
    await expect(page.locator("h1")).toHaveText("Overview");
    await expect(
      page.getByText("CryptoAgent pipeline status and portfolio summary")
    ).toBeVisible();
  });

  test("stat cards show seeded data", async ({ page }) => {
    await expect(page.getByText("Net Worth")).toBeVisible();
    await expect(page.getByText("Total Trades")).toBeVisible();
    await expect(page.getByText("Signals Logged")).toBeVisible();
    await expect(page.getByText("Market Regime")).toBeVisible();

    const main = page.locator("main");
    await expect(main.getByText("7", { exact: true })).toBeVisible();
    await expect(main.getByText("26", { exact: true })).toBeVisible();
  });

  test("recent trades card shows trade rows", async ({ page }) => {
    await expect(page.getByText("Recent Trades")).toBeVisible();
    await expect(page.getByText("SOL").first()).toBeVisible();
  });

  test("recent reflections card shows entries", async ({ page }) => {
    await expect(page.getByText("Recent Reflections")).toBeVisible();
    await expect(page.getByText("Level 1").first()).toBeVisible();
  });

  test("run pipeline button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /Run Pipeline/i })
    ).toBeVisible();
  });

  test("run trigger handles success", async ({ page }) => {
    await page.route("**/api/run", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "Pipeline triggered" }),
      })
    );
    await page.getByRole("button", { name: /Run Pipeline/i }).click();
    await expect(page.getByText("Pipeline triggered")).toBeVisible();
  });

  test("run trigger handles error", async ({ page }) => {
    await page.route("**/api/run", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ error: "SIDECAR_URL not configured" }),
      })
    );
    await page.getByRole("button", { name: /Run Pipeline/i }).click();
    await expect(page.getByText("SIDECAR_URL not configured")).toBeVisible();
  });
});
