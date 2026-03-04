"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { SignalAccuracy } from "@/lib/types";

interface SignalChartProps {
  accuracy: SignalAccuracy[];
}

export function SignalChart({ accuracy }: SignalChartProps) {
  if (accuracy.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No signal outcome data yet. Run more cycles to populate.
      </p>
    );
  }

  // Group by timeframe for separate charts
  const timeframes = [...new Set(accuracy.map((a) => a.timeframe))];

  return (
    <div className="space-y-6">
      {timeframes.map((tf) => {
        const data = accuracy
          .filter((a) => a.timeframe === tf)
          .sort((a, b) => b.hitRate - a.hitRate);

        return (
          <div key={tf}>
            <h3 className="mb-2 text-sm font-medium">
              {tf} Accuracy
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={{ fill: "#888", fontSize: 12 }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={120}
                  tick={{ fill: "#888", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid #333",
                    borderRadius: "6px",
                  }}
                  formatter={(value: number | undefined) => [
                    `${value ?? 0}%`,
                    "Hit Rate",
                  ]}
                />
                <Bar dataKey="hitRate" radius={[0, 4, 4, 0]}>
                  {data.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={
                        entry.hitRate >= 60
                          ? "#22c55e"
                          : entry.hitRate >= 45
                            ? "#eab308"
                            : "#ef4444"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
}
