import { db } from "@/lib/db";
import { signals, signalOutcomes } from "@/lib/schema";
import { desc, eq, sql } from "drizzle-orm";
import { SignalChart } from "@/components/signal-chart";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function SignalsPage() {
  const [rows, accuracyRows] = await Promise.all([
    db.select().from(signals).orderBy(desc(signals.id)).limit(100),
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Signals</h1>
        <p className="text-sm text-muted-foreground">
          Signal accuracy and history across 17 extracted signals
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Signal Accuracy by Timeframe
          </CardTitle>
        </CardHeader>
        <CardContent>
          <SignalChart accuracy={accuracy} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Signal History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Confidence</TableHead>
                  <TableHead className="text-right">Raw Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center">
                      No signals yet
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell className="text-xs">
                        {s.timestamp?.slice(0, 16).replace("T", " ")}
                      </TableCell>
                      <TableCell className="font-medium">{s.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {s.source}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={cn(
                            "text-xs",
                            s.direction === "bullish" &&
                              "bg-green-600 hover:bg-green-700",
                            s.direction === "bearish" &&
                              "bg-red-600 hover:bg-red-700",
                            s.direction === "neutral" &&
                              "bg-muted text-muted-foreground hover:bg-muted"
                          )}
                        >
                          {s.direction}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {(s.confidence * 100).toFixed(0)}%
                      </TableCell>
                      <TableCell className="text-right">
                        {s.rawValue?.toFixed(4) ?? "—"}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
