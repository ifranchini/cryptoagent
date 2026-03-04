import { createOpenAI } from "@ai-sdk/openai";
import { streamText } from "ai";
import { db } from "@/lib/db";
import { trades, reflections, signals, signalOutcomes } from "@/lib/schema";
import { desc, eq, sql } from "drizzle-orm";

export const maxDuration = 60;

const openrouter = createOpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function buildContext(): Promise<string> {
  const [recentTrades, recentReflections, accuracy] = await Promise.all([
    db.select().from(trades).orderBy(desc(trades.id)).limit(5),
    db.select().from(reflections).orderBy(desc(reflections.id)).limit(5),
    db
      .select({
        name: signals.name,
        timeframe: signalOutcomes.timeframe,
        total: sql<number>`count(*)`,
        correct: sql<number>`sum(case when ${signalOutcomes.directionCorrect} then 1 else 0 end)`,
      })
      .from(signalOutcomes)
      .innerJoin(signals, eq(signalOutcomes.signalId, signals.id))
      .groupBy(signals.name, signalOutcomes.timeframe),
  ]);

  const latestTrade = recentTrades[0];
  const regime = latestTrade?.regime ?? "unknown";

  const parts = [
    `Current market regime: ${regime}`,
    "",
    "Recent trades:",
    ...recentTrades.map(
      (t) =>
        `  ${t.timestamp} | ${t.action} ${t.token} | price=$${t.price} | conf=${t.confidence}/10 | regime=${t.regime}`
    ),
    "",
    "Signal accuracy:",
    ...accuracy.map(
      (a) =>
        `  ${a.name} (${a.timeframe}): ${a.total > 0 ? Math.round((a.correct / a.total) * 100) : "N/A"}% hit rate (${a.total} samples)`
    ),
    "",
    "Recent reflections:",
    ...recentReflections.map(
      (r) => `  [L${r.level}] ${r.timestamp}: ${r.text.slice(0, 200)}`
    ),
  ];

  return parts.join("\n");
}

export async function POST(req: Request) {
  const { messages } = await req.json();
  const context = await buildContext();

  const result = streamText({
    model: openrouter("anthropic/claude-sonnet-4"),
    system: `You are a CryptoAgent assistant — an AI that helps analyze a multi-agent LLM crypto trading system.

You have access to the system's live data:

${context}

Architecture: 5 agents (Research, Sentiment, Macro, Brain, Trader) orchestrated via LangGraph. Brain synthesizes analyst reports and makes BUY/SELL/HOLD decisions with confidence 1-10. Paper trading only.

Help the user understand:
- Why the system made specific trading decisions
- Which signals are most/least accurate
- What the reflections suggest about strategy adjustments
- Market regime implications
- Risk management insights

Be concise and data-driven. Reference specific numbers from the data above.`,
    messages,
  });

  return result.toTextStreamResponse();
}
