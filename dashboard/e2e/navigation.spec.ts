import { test, expect } from "@playwright/test";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/trades", label: "Trades" },
  { href: "/signals", label: "Signals" },
  { href: "/reflections", label: "Reflections" },
  { href: "/chat", label: "Chat" },
];

test.describe("Sidebar Navigation", () => {
  test("shows brand, all nav links, and footer", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("aside");
    await expect(sidebar.getByText("CryptoAgent")).toBeVisible();
    for (const { label } of NAV_ITEMS) {
      await expect(sidebar.getByRole("link", { name: label })).toBeVisible();
    }
    await expect(sidebar.getByText("Paper Trading")).toBeVisible();
  });

  test("Overview link is active on homepage", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("aside").getByRole("link", { name: "Overview" });
    await expect(link).toHaveClass(/bg-accent/);
  });

  for (const { href, label } of NAV_ITEMS) {
    test(`clicking "${label}" navigates to ${href}`, async ({ page }) => {
      await page.goto("/");
      await page.locator("aside").getByRole("link", { name: label }).click();
      await page.waitForURL(href === "/" ? "/" : `${href}**`);
      const heading = page.locator("h1");
      await expect(heading).toHaveText(label);
    });
  }
});
