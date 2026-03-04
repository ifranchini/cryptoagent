import { db } from "@/lib/db";
import { trades, reflections, signals } from "@/lib/schema";
import { desc, sql, count } from "drizzle-orm";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const [recentTrades, recentReflections, tradeCount, signalCount] =
    await Promise.all([
      db.select().from(trades).orderBy(desc(trades.id)).limit(5),
      db.select().from(reflections).orderBy(desc(reflections.id)).limit(3),
      db.select({ value: count() }).from(trades),
      db.select({ value: count() }).from(signals),
    ]);

  const latestTrade = recentTrades[0] ?? null;
  let portfolio = null;
  if (latestTrade?.portfolioSnapshot) {
    try {
      portfolio = JSON.parse(latestTrade.portfolioSnapshot);
    } catch {
      /* ignore parse errors */
    }
  }

  // Win rate: trades where action was BUY/SELL and confidence >= 6
  const winTrades = await db
    .select({ value: count() })
    .from(trades)
    .where(sql`${trades.confidence} >= 6 AND ${trades.action} != 'HOLD'`);

  const actionTrades = await db
    .select({ value: count() })
    .from(trades)
    .where(sql`${trades.action} != 'HOLD'`);

  const totalActions = actionTrades[0]?.value ?? 0;
  const winRate =
    totalActions > 0 ? ((winTrades[0]?.value ?? 0) / totalActions) * 100 : 0;

  return NextResponse.json({
    latestTrade,
    portfolio,
    recentTrades,
    recentReflections,
    stats: {
      totalTrades: tradeCount[0]?.value ?? 0,
      totalSignals: signalCount[0]?.value ?? 0,
      winRate: Math.round(winRate),
      latestRegime: latestTrade?.regime ?? "unknown",
    },
  });
}
