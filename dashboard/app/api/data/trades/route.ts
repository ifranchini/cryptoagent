import { db } from "@/lib/db";
import { trades } from "@/lib/schema";
import { desc, eq, and, sql } from "drizzle-orm";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const token = params.get("token");
  const action = params.get("action");
  const limit = parseInt(params.get("limit") ?? "50", 10);
  const offset = parseInt(params.get("offset") ?? "0", 10);

  const conditions = [];
  if (token) conditions.push(eq(trades.token, token));
  if (action) conditions.push(eq(trades.action, action));

  const where = conditions.length > 0 ? and(...conditions) : undefined;

  const [rows, total] = await Promise.all([
    db
      .select()
      .from(trades)
      .where(where)
      .orderBy(desc(trades.id))
      .limit(limit)
      .offset(offset),
    db
      .select({ value: sql<number>`count(*)` })
      .from(trades)
      .where(where),
  ]);

  return NextResponse.json({
    trades: rows,
    total: total[0]?.value ?? 0,
    limit,
    offset,
  });
}
