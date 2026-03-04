import { test, expect } from "@playwright/test";

test.describe("Trades Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/trades");
  });

  test("renders heading and subtitle", async ({ page }) => {
    await expect(page.locator("h1")).toHaveText("Trades");
    await expect(
      page.getByText("All trade history from the pipeline")
    ).toBeVisible();
  });

  test("table has correct headers", async ({ page }) => {
    const headers = ["Time", "Action", "Token", "Price", "Quantity", "Fee", "Regime", "Conf"];
    for (const h of headers) {
      await expect(
        page.locator("thead th", { hasText: h }).first()
      ).toBeVisible();
    }
  });

  test("table shows seeded trade rows", async ({ page }) => {
    const rows = page.locator("tbody tr");
    await expect(rows).toHaveCount(7);
    await expect(rows.first().getByText("SOL")).toBeVisible();
  });

  test("detail panel shows placeholder before selection", async ({ page }) => {
    await expect(page.getByText("Trade Detail")).toBeVisible();
    await expect(
      page.getByText("Click a trade to view details")
    ).toBeVisible();
  });

  test("clicking a row shows brain decision and portfolio snapshot", async ({ page }) => {
    await page.locator("tbody tr").first().click();
    await expect(page.getByText("Brain Decision")).toBeVisible();
    await expect(page.getByText("Portfolio Snapshot")).toBeVisible();
    await expect(page.locator("pre").first()).toBeVisible();
  });
});
