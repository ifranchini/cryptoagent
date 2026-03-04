import { db } from "@/lib/db";
import { trades } from "@/lib/schema";
import { desc } from "drizzle-orm";
import { TradeTable } from "@/components/trade-table";

export const dynamic = "force-dynamic";

export default async function TradesPage() {
  const rows = await db
    .select()
    .from(trades)
    .orderBy(desc(trades.id))
    .limit(100);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Trades</h1>
        <p className="text-sm text-muted-foreground">
          All trade history from the pipeline
        </p>
      </div>
      <TradeTable trades={rows} />
    </div>
  );
}
