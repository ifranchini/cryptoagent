import { db } from "@/lib/db";
import { signals, signalOutcomes } from "@/lib/schema";
import { desc, eq, sql } from "drizzle-orm";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const limit = parseInt(params.get("limit") ?? "100", 10);
  const offset = parseInt(params.get("offset") ?? "0", 10);

  const [rows, accuracyRows] = await Promise.all([
    db
      .select()
      .from(signals)
      .orderBy(desc(signals.id))
      .limit(limit)
      .offset(offset),
    db
      .select({
        name: signals.name,
        source: signals.source,
        timeframe: signalOutcomes.timeframe,
        total: sql<number>`count(*)`,
        correct: sql<number>`sum(case when ${signalOutcomes.directionCorrect} then 1 else 0 end)`,
      })
      .from(signalOutcomes)
      .innerJoin(signals, eq(signalOutcomes.signalId, signals.id))
      .groupBy(signals.name, signals.source, signalOutcomes.timeframe),
  ]);

  const accuracy = accuracyRows.map((r) => ({
    name: r.name,
    source: r.source,
    timeframe: r.timeframe,
    total: r.total,
    correct: r.correct,
    hitRate: r.total > 0 ? Math.round((r.correct / r.total) * 100) : 0,
  }));

  return NextResponse.json({ signals: rows, accuracy });
}
