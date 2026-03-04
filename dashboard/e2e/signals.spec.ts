import { test, expect } from "@playwright/test";

test.describe("Signals Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/signals");
  });

  test("renders heading and subtitle", async ({ page }) => {
    await expect(page.locator("h1")).toHaveText("Signals");
    await expect(
      page.getByText("Signal accuracy and history across 17 extracted signals")
    ).toBeVisible();
  });

  test("accuracy chart renders with bars", async ({ page }) => {
    await expect(page.getByText("Signal Accuracy by Timeframe")).toBeVisible();
    await expect(page.getByText("4h Accuracy")).toBeVisible();
    const svg = page.locator(".recharts-wrapper svg").first();
    await expect(svg).toBeVisible();
  });

  test("signal history table has correct headers", async ({ page }) => {
    await expect(page.getByText("Signal History")).toBeVisible();
    const headers = ["Time", "Name", "Source", "Direction", "Confidence", "Raw Value"];
    for (const h of headers) {
      await expect(
        page.locator("thead th", { hasText: h }).first()
      ).toBeVisible();
    }
  });

  test("signal history table shows seeded data", async ({ page }) => {
    const rows = page.locator("tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(26);
  });
});
