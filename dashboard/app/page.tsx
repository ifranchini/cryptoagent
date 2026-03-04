import { db } from "@/lib/db";
import { trades, reflections, signals } from "@/lib/schema";
import { desc, count } from "drizzle-orm";
import { StatCard } from "@/components/stat-card";
import { RegimeBadge } from "@/components/regime-badge";
import { ActionBadge } from "@/components/action-badge";
import { RunTrigger } from "@/components/run-trigger";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ArrowRightLeft,
  Signal,
  TrendingUp,
  Activity,
} from "lucide-react";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  const [recentTrades, recentReflections, tradeCount, signalCount] =
    await Promise.all([
      db.select().from(trades).orderBy(desc(trades.id)).limit(5),
      db.select().from(reflections).orderBy(desc(reflections.id)).limit(3),
      db.select({ value: count() }).from(trades),
      db.select({ value: count() }).from(signals),
    ]);

  const latestTrade = recentTrades[0] ?? null;
  let portfolio: { cash?: number; net_worth?: number } | null = null;
  if (latestTrade?.portfolioSnapshot) {
    try {
      portfolio = JSON.parse(latestTrade.portfolioSnapshot);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Overview</h1>
          <p className="text-sm text-muted-foreground">
            CryptoAgent pipeline status and portfolio summary
          </p>
        </div>
        <RunTrigger />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Net Worth"
          value={
            portfolio?.net_worth
              ? `$${portfolio.net_worth.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
              : "No data"
          }
          subtitle={
            portfolio?.cash
              ? `$${portfolio.cash.toLocaleString(undefined, { maximumFractionDigits: 2 })} cash`
              : undefined
          }
          icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          title="Total Trades"
          value={tradeCount[0]?.value ?? 0}
          subtitle={`Latest: ${latestTrade?.action ?? "none"}`}
          icon={
            <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
          }
        />
        <StatCard
          title="Signals Logged"
          value={signalCount[0]?.value ?? 0}
          icon={<Signal className="h-4 w-4 text-muted-foreground" />}
        />
        <div>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Market Regime
              </CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <RegimeBadge regime={latestTrade?.regime} />
              <p className="mt-2 text-xs text-muted-foreground">
                {latestTrade?.timestamp?.slice(0, 10) ?? "No data"}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Trades</CardTitle>
          </CardHeader>
          <CardContent>
            {recentTrades.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No trades yet. Run the pipeline to get started.
              </p>
            ) : (
              <div className="space-y-3">
                {recentTrades.map((t) => (
                  <div
                    key={t.id}
                    className="flex items-center justify-between text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <ActionBadge action={t.action} />
                      <span className="font-medium">{t.token}</span>
                      <span className="text-muted-foreground">
                        ${t.price?.toFixed(2) ?? "—"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <RegimeBadge regime={t.regime} />
                      <span className="text-xs text-muted-foreground">
                        {t.timestamp?.slice(0, 16).replace("T", " ")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Reflections</CardTitle>
          </CardHeader>
          <CardContent>
            {recentReflections.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No reflections yet.
              </p>
            ) : (
              <div className="space-y-3">
                {recentReflections.map((r) => (
                  <div key={r.id} className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium">
                        Level {r.level}
                      </span>
                      <RegimeBadge regime={r.regime} />
                      <span className="text-xs text-muted-foreground">
                        {r.timestamp?.slice(0, 16).replace("T", " ")}
                      </span>
                    </div>
                    <p className="line-clamp-2 text-sm text-muted-foreground">
                      {r.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
