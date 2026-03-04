import { db } from "@/lib/db";
import { reflections } from "@/lib/schema";
import { desc } from "drizzle-orm";
import { RegimeBadge } from "@/components/regime-badge";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const dynamic = "force-dynamic";

export default async function ReflectionsPage() {
  const rows = await db
    .select()
    .from(reflections)
    .orderBy(desc(reflections.id))
    .limit(50);

  const level1 = rows.filter((r) => r.level === 1);
  const level2 = rows.filter((r) => r.level === 2);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Reflections</h1>
        <p className="text-sm text-muted-foreground">
          Per-cycle tactical (L1) and cross-trial strategic (L2) reflections
        </p>
      </div>

      {level2.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Cross-Trial Reviews (L2)</h2>
          {level2.map((r) => (
            <Card key={r.id} className="border-chart-1/30">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Badge className="bg-chart-1">Level 2</Badge>
                  <RegimeBadge regime={r.regime} />
                  <span className="text-xs text-muted-foreground">
                    {r.timestamp?.slice(0, 16).replace("T", " ")}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{r.text}</p>
                {r.performanceSummary && (
                  <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">
                    {r.performanceSummary}
                  </pre>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Per-Cycle Reflections (L1)</h2>
        {level1.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No reflections yet. Run the pipeline to generate them.
          </p>
        ) : (
          level1.map((r) => (
            <Card key={r.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Level 1</Badge>
                  <RegimeBadge regime={r.regime} />
                  <span className="text-xs text-muted-foreground">
                    {r.timestamp?.slice(0, 16).replace("T", " ")}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{r.text}</p>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
