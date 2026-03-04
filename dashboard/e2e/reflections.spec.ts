import { test, expect } from "@playwright/test";

test.describe("Reflections Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/reflections");
  });

  test("renders heading and subtitle", async ({ page }) => {
    await expect(page.locator("h1")).toHaveText("Reflections");
    await expect(
      page.getByText(
        "Per-cycle tactical (L1) and cross-trial strategic (L2) reflections"
      )
    ).toBeVisible();
  });

  test("Level 2 section renders with card", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Cross-Trial Reviews (L2)" })
    ).toBeVisible();
    const l2Badge = page.getByText("Level 2", { exact: true });
    await expect(l2Badge.first()).toBeVisible();
  });

  test("Level 1 section renders with cards", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Per-Cycle Reflections (L1)" })
    ).toBeVisible();
    const l1Badges = page.getByText("Level 1", { exact: true });
    await expect(l1Badges).toHaveCount(4);
  });

  test("reflection cards have non-empty text", async ({ page }) => {
    const cards = page.locator("[data-slot='card-content'] p");
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(5);
    for (let i = 0; i < count; i++) {
      const text = await cards.nth(i).textContent();
      expect(text?.trim().length).toBeGreaterThan(0);
    }
  });
});
