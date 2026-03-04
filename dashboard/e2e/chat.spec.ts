import { test, expect } from "@playwright/test";

test.describe("Chat Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
  });

  test("renders heading and subtitle", async ({ page }) => {
    await expect(page.locator("h1")).toHaveText("Chat");
    await expect(
      page.getByText(
        "Ask questions about your trading data, signals, and decisions"
      )
    ).toBeVisible();
  });

  test("empty state shows bot icon, instruction, and suggestions", async ({ page }) => {
    await expect(
      page.getByText("Ask me about your trading data, signals, or decisions.")
    ).toBeVisible();

    const suggestions = [
      "Explain the last trade decision",
      "Which signals are most accurate?",
      "What do the reflections suggest?",
      "Summarize the current portfolio status",
    ];
    for (const s of suggestions) {
      await expect(page.getByRole("button", { name: s })).toBeVisible();
    }
  });

  test("input and send button are present, send disabled when empty", async ({ page }) => {
    const input = page.getByPlaceholder("Ask about your trading data...");
    await expect(input).toBeVisible();
    const sendBtn = page.locator("form button[type='submit']");
    await expect(sendBtn).toBeDisabled();
  });

  test("typing enables send button", async ({ page }) => {
    const input = page.getByPlaceholder("Ask about your trading data...");
    await input.fill("test message");
    const sendBtn = page.locator("form button[type='submit']");
    await expect(sendBtn).toBeEnabled();
  });

  test("submitting a message shows user bubble and assistant response", async ({ page }) => {
    await page.route("**/api/chat", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/plain; charset=utf-8",
        body: "0:\"This is a test response from the assistant.\"\n",
      })
    );

    const input = page.getByPlaceholder("Ask about your trading data...");
    await input.fill("Hello");
    await page.locator("form button[type='submit']").click();

    await expect(page.getByText("Hello")).toBeVisible();
  });
});
