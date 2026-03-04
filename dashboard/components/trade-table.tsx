"use client";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ActionBadge } from "@/components/action-badge";
import { RegimeBadge } from "@/components/regime-badge";
import type { Trade } from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface TradeTableProps {
  trades: Trade[];
}

export function TradeTable({ trades }: TradeTableProps) {
  const [selected, setSelected] = useState<Trade | null>(null);

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Token</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead className="text-right">Fee</TableHead>
                <TableHead>Regime</TableHead>
                <TableHead className="text-right">Conf</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">
                    No trades found
                  </TableCell>
                </TableRow>
              ) : (
                trades.map((t) => (
                  <TableRow
                    key={t.id}
                    className="cursor-pointer"
                    onClick={() => setSelected(t)}
                  >
                    <TableCell className="text-xs">
                      {t.timestamp?.slice(0, 16).replace("T", " ")}
                    </TableCell>
                    <TableCell>
                      <ActionBadge action={t.action} />
                    </TableCell>
                    <TableCell className="font-medium">{t.token}</TableCell>
                    <TableCell className="text-right">
                      ${t.price?.toFixed(2) ?? "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      {t.quantity?.toFixed(4) ?? "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      ${t.fee?.toFixed(4) ?? "—"}
                    </TableCell>
                    <TableCell>
                      <RegimeBadge regime={t.regime} />
                    </TableCell>
                    <TableCell className="text-right">
                      {t.confidence ?? "—"}/10
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Trade Detail</CardTitle>
          </CardHeader>
          <CardContent>
            {selected ? (
              <TradeDetail trade={selected} />
            ) : (
              <p className="text-sm text-muted-foreground">
                Click a trade to view details
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TradeDetail({ trade }: { trade: Trade }) {
  let brain: Record<string, unknown> | null = null;
  let portfolio: Record<string, unknown> | null = null;

  if (trade.brainDecision) {
    try {
      brain = JSON.parse(trade.brainDecision);
    } catch {
      /* ignore */
    }
  }
  if (trade.portfolioSnapshot) {
    try {
      portfolio = JSON.parse(trade.portfolioSnapshot);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="space-y-4 text-sm">
      <div>
        <h4 className="mb-1 font-medium">Brain Decision</h4>
        {brain ? (
          <pre className="overflow-auto rounded bg-muted p-2 text-xs">
            {JSON.stringify(brain, null, 2)}
          </pre>
        ) : (
          <p className="text-muted-foreground">No brain decision data</p>
        )}
      </div>
      <div>
        <h4 className="mb-1 font-medium">Portfolio Snapshot</h4>
        {portfolio ? (
          <pre className="overflow-auto rounded bg-muted p-2 text-xs">
            {JSON.stringify(portfolio, null, 2)}
          </pre>
        ) : (
          <p className="text-muted-foreground">No portfolio data</p>
        )}
      </div>
    </div>
  );
}
