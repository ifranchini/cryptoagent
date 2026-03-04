import {
  pgTable,
  serial,
  text,
  real,
  integer,
  boolean,
  timestamp,
} from "drizzle-orm/pg-core";

export const trades = pgTable("trades", {
  id: serial("id").primaryKey(),
  timestamp: text("timestamp").notNull(),
  token: text("token").notNull(),
  action: text("action").notNull(),
  price: real("price"),
  quantity: real("quantity"),
  fee: real("fee"),
  portfolioSnapshot: text("portfolio_snapshot"),
  brainDecision: text("brain_decision"),
  regime: text("regime"),
  confidence: integer("confidence"),
});

export const reflections = pgTable("reflections", {
  id: serial("id").primaryKey(),
  timestamp: text("timestamp").notNull(),
  level: integer("level").notNull(),
  text: text("text").notNull(),
  regime: text("regime"),
  performanceSummary: text("performance_summary"),
});

export const signals = pgTable("signals", {
  id: serial("id").primaryKey(),
  timestamp: text("timestamp").notNull(),
  token: text("token").notNull(),
  name: text("name").notNull(),
  source: text("source").notNull(),
  direction: text("direction").notNull(),
  confidence: real("confidence").notNull(),
  rawValue: real("raw_value"),
});

export const priceSnapshots = pgTable("price_snapshots", {
  id: serial("id").primaryKey(),
  timestamp: text("timestamp").notNull(),
  token: text("token").notNull(),
  price: real("price").notNull(),
  volume24h: real("volume_24h"),
});

export const signalOutcomes = pgTable("signal_outcomes", {
  id: serial("id").primaryKey(),
  signalId: integer("signal_id")
    .notNull()
    .references(() => signals.id),
  timeframe: text("timeframe").notNull(),
  priceAtSignal: real("price_at_signal").notNull(),
  priceAtEval: real("price_at_eval").notNull(),
  priceChangePct: real("price_change_pct").notNull(),
  directionCorrect: boolean("direction_correct").notNull(),
  evaluatedAt: text("evaluated_at").notNull(),
});

export type Trade = typeof trades.$inferSelect;
export type Reflection = typeof reflections.$inferSelect;
export type Signal = typeof signals.$inferSelect;
export type PriceSnapshot = typeof priceSnapshots.$inferSelect;
export type SignalOutcome = typeof signalOutcomes.$inferSelect;
