import { db } from "@/lib/db";
import { reflections } from "@/lib/schema";
import { desc, eq } from "drizzle-orm";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const level = params.get("level");
  const limit = parseInt(params.get("limit") ?? "50", 10);

  const where = level ? eq(reflections.level, parseInt(level, 10)) : undefined;

  const rows = await db
    .select()
    .from(reflections)
    .where(where)
    .orderBy(desc(reflections.id))
    .limit(limit);

  return NextResponse.json({ reflections: rows });
}
