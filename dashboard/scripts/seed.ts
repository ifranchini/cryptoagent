import { neon } from "@neondatabase/serverless";

const DATABASE_URL = process.env.DATABASE_URL!;
const sql = neon(DATABASE_URL);

async function seed() {
  console.log("Seeding database...");

  // Sample trades
  const trades = [
    { ts: "2026-03-01T10:00:00Z", token: "SOL", action: "BUY", price: 142.50, qty: 3.5, fee: 0.50, regime: "bull", confidence: 8, portfolio: { cash: 7501.25, holdings: { SOL: 3.5 }, net_worth: 10000 } , brain: { action: "BUY", asset: "SOL", size_pct: 0.25, stop_loss_pct: 5, take_profit_pct: 15, confidence: 8, regime: "bull", rationale: "Strong RSI divergence with increasing TVL and whale accumulation. Macro is risk-on with M2 expanding." } },
    { ts: "2026-03-01T14:00:00Z", token: "SOL", action: "HOLD", price: 144.20, qty: 0, fee: 0, regime: "bull", confidence: 6, portfolio: { cash: 7501.25, holdings: { SOL: 3.5 }, net_worth: 10046.95 }, brain: { action: "HOLD", asset: "SOL", size_pct: 0, confidence: 6, regime: "bull", rationale: "Momentum intact but RSI approaching overbought. Wait for pullback to add." } },
    { ts: "2026-03-01T18:00:00Z", token: "SOL", action: "BUY", price: 139.80, qty: 2.0, fee: 0.28, regime: "sideways", confidence: 7, portfolio: { cash: 7221.37, holdings: { SOL: 5.5 }, net_worth: 9990.27 }, brain: { action: "BUY", asset: "SOL", size_pct: 0.15, confidence: 7, regime: "sideways", rationale: "Pullback to SMA20 support with strong on-chain metrics. Good entry for DCA." } },
    { ts: "2026-03-02T10:00:00Z", token: "SOL", action: "HOLD", price: 141.30, qty: 0, fee: 0, regime: "sideways", confidence: 5, portfolio: { cash: 7221.37, holdings: { SOL: 5.5 }, net_worth: 9998.52 }, brain: { action: "HOLD", asset: "SOL", size_pct: 0, confidence: 5, regime: "sideways", rationale: "Mixed signals. RSI neutral, macro uncertain with upcoming FOMC. Maintain position." } },
    { ts: "2026-03-02T14:00:00Z", token: "SOL", action: "SELL", price: 148.50, qty: 2.0, fee: 0.30, regime: "bull", confidence: 7, portfolio: { cash: 7517.77, holdings: { SOL: 3.5 }, net_worth: 10037.52 }, brain: { action: "SELL", asset: "SOL", size_pct: 0.10, confidence: 7, regime: "bull", rationale: "Take partial profits at resistance. RSI overbought, Bollinger band squeeze." } },
    { ts: "2026-03-02T18:00:00Z", token: "SOL", action: "HOLD", price: 147.20, qty: 0, fee: 0, regime: "bull", confidence: 6, portfolio: { cash: 7517.77, holdings: { SOL: 3.5 }, net_worth: 10032.97 }, brain: { action: "HOLD", asset: "SOL", size_pct: 0, confidence: 6, regime: "bull", rationale: "Healthy consolidation after profit-taking. On-chain still strong." } },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", action: "BUY", price: 145.00, qty: 1.5, fee: 0.22, regime: "bull", confidence: 8, portfolio: { cash: 7300.05, holdings: { SOL: 5.0 }, net_worth: 10025.05 }, brain: { action: "BUY", asset: "SOL", size_pct: 0.12, confidence: 8, regime: "bull", rationale: "Whale accumulation detected. MACD crossover confirmed. Fear & Greed at 72 (greed but not extreme)." } },
  ];

  for (const t of trades) {
    await sql`INSERT INTO trades (timestamp, token, action, price, quantity, fee, portfolio_snapshot, brain_decision, regime, confidence)
      VALUES (${t.ts}, ${t.token}, ${t.action}, ${t.price}, ${t.qty}, ${t.fee}, ${JSON.stringify(t.portfolio)}, ${JSON.stringify(t.brain)}, ${t.regime}, ${t.confidence})`;
  }
  console.log(`  Inserted ${trades.length} trades`);

  // Sample reflections
  const reflections = [
    { ts: "2026-03-01T14:05:00Z", level: 1, text: "Initial BUY entry at $142.50 was well-timed — caught the RSI divergence before the move to $144. On-chain metrics (TVL +3.2%, whale accumulation) confirmed the signal. Should maintain this approach of requiring multi-source confirmation before entry.", regime: "bull", summary: "" },
    { ts: "2026-03-01T18:05:00Z", level: 1, text: "DCA buy on the pullback to SMA20 at $139.80. The regime shifted to sideways briefly but on-chain strength remained. Good discipline to add on dips rather than chase. Fee impact was minimal at $0.28.", regime: "sideways", summary: "" },
    { ts: "2026-03-02T14:05:00Z", level: 1, text: "Partial profit-taking at $148.50 was the right call — RSI was overbought at 74 and Bollinger bands were squeezing. Keeping 3.5 SOL core position for continued upside. Risk management working as intended.", regime: "bull", summary: "" },
    { ts: "2026-03-03T10:05:00Z", level: 1, text: "Re-entry at $145.00 after consolidation. Whale signals were the key differentiator this cycle — large wallet accumulation preceded the bounce. MACD crossover added confirmation. Fear & Greed at 72 is elevated but not at extreme levels that warrant caution.", regime: "bull", summary: "" },
    { ts: "2026-03-03T10:10:00Z", level: 2, text: "Strategic review after 5 cycles: The multi-source confirmation approach is working well. Key patterns: (1) On-chain whale signals have been the most reliable entry indicator, correctly predicting 3/3 bounces. (2) RSI overbought readings at 70+ have been effective profit-taking signals. (3) Regime transitions from sideways→bull offered the best risk/reward entries. (4) DCA on dips to SMA20 produced better average entries than chasing breakouts. Adjustment: increase position sizing confidence when whale + technical signals align. Reduce exposure when RSI > 75 even in bull regime.", regime: "bull", summary: "5 cycles, 3 BUY, 1 SELL, 2 HOLD. Net P&L: +$25.05 (+0.25%). Win rate: 75% on active trades." },
  ];

  for (const r of reflections) {
    await sql`INSERT INTO reflections (timestamp, level, text, regime, performance_summary)
      VALUES (${r.ts}, ${r.level}, ${r.text}, ${r.regime}, ${r.summary})`;
  }
  console.log(`  Inserted ${reflections.length} reflections`);

  // Sample signals
  const signalData = [
    // Cycle 1 signals
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "rsi_14", source: "technical", direction: "bullish", conf: 0.72, raw: 38.5 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "macd_histogram", source: "technical", direction: "bullish", conf: 0.65, raw: 1.2 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "price_vs_sma20", source: "technical", direction: "bearish", conf: 0.55, raw: -0.8 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "price_vs_sma50", source: "technical", direction: "bullish", conf: 0.60, raw: 2.1 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "bollinger_position", source: "technical", direction: "neutral", conf: 0.50, raw: 0.45 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "tvl_trend", source: "onchain", direction: "bullish", conf: 0.80, raw: 3.2 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "whale_activity", source: "onchain", direction: "bullish", conf: 0.85, raw: 1.0 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "dex_volume_change", source: "onchain", direction: "bullish", conf: 0.70, raw: 12.5 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "fear_greed_contrarian", source: "sentiment", direction: "neutral", conf: 0.50, raw: 55.0 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "reddit_sentiment", source: "sentiment", direction: "bullish", conf: 0.62, raw: 0.65 },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "macro_regime", source: "macro", direction: "bullish", conf: 0.70, raw: null },
    { ts: "2026-03-01T10:00:00Z", token: "SOL", name: "market_regime", source: "macro", direction: "bullish", conf: 0.75, raw: null },
    // Cycle 3 signals
    { ts: "2026-03-02T14:00:00Z", token: "SOL", name: "rsi_14", source: "technical", direction: "bearish", conf: 0.70, raw: 74.2 },
    { ts: "2026-03-02T14:00:00Z", token: "SOL", name: "macd_histogram", source: "technical", direction: "bullish", conf: 0.55, raw: 0.3 },
    { ts: "2026-03-02T14:00:00Z", token: "SOL", name: "tvl_trend", source: "onchain", direction: "bullish", conf: 0.78, raw: 2.8 },
    { ts: "2026-03-02T14:00:00Z", token: "SOL", name: "whale_activity", source: "onchain", direction: "bullish", conf: 0.82, raw: 1.0 },
    { ts: "2026-03-02T14:00:00Z", token: "SOL", name: "fear_greed_contrarian", source: "sentiment", direction: "bearish", conf: 0.60, raw: 72.0 },
    // Cycle 5 signals
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "rsi_14", source: "technical", direction: "bullish", conf: 0.68, raw: 52.1 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "macd_histogram", source: "technical", direction: "bullish", conf: 0.72, raw: 1.8 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "price_vs_sma20", source: "technical", direction: "bullish", conf: 0.65, raw: 1.2 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "tvl_trend", source: "onchain", direction: "bullish", conf: 0.82, raw: 4.1 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "whale_activity", source: "onchain", direction: "bullish", conf: 0.90, raw: 1.0 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "dex_volume_change", source: "onchain", direction: "bullish", conf: 0.75, raw: 18.3 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "fear_greed_contrarian", source: "sentiment", direction: "neutral", conf: 0.48, raw: 72.0 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "reddit_sentiment", source: "sentiment", direction: "bullish", conf: 0.70, raw: 0.78 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", name: "macro_regime", source: "macro", direction: "bullish", conf: 0.72, raw: null },
  ];

  for (const s of signalData) {
    await sql`INSERT INTO signals (timestamp, token, name, source, direction, confidence, raw_value)
      VALUES (${s.ts}, ${s.token}, ${s.name}, ${s.source}, ${s.direction}, ${s.conf}, ${s.raw})`;
  }
  console.log(`  Inserted ${signalData.length} signals`);

  // Price snapshots
  const prices = [
    { ts: "2026-03-01T10:00:00Z", token: "SOL", price: 142.50, vol: 1250000000 },
    { ts: "2026-03-01T14:00:00Z", token: "SOL", price: 144.20, vol: 1180000000 },
    { ts: "2026-03-01T18:00:00Z", token: "SOL", price: 139.80, vol: 1420000000 },
    { ts: "2026-03-02T10:00:00Z", token: "SOL", price: 141.30, vol: 980000000 },
    { ts: "2026-03-02T14:00:00Z", token: "SOL", price: 148.50, vol: 1560000000 },
    { ts: "2026-03-02T18:00:00Z", token: "SOL", price: 147.20, vol: 1100000000 },
    { ts: "2026-03-03T10:00:00Z", token: "SOL", price: 145.00, vol: 1320000000 },
  ];

  for (const p of prices) {
    await sql`INSERT INTO price_snapshots (timestamp, token, price, volume_24h)
      VALUES (${p.ts}, ${p.token}, ${p.price}, ${p.vol})`;
  }
  console.log(`  Inserted ${prices.length} price snapshots`);

  // Signal outcomes (for accuracy charts)
  // Get signal IDs from DB
  const allSignals = await sql`SELECT id, name, timestamp FROM signals ORDER BY id`;

  const outcomes = [];
  for (const sig of allSignals) {
    // Simulate 4h outcome for all signals
    const priceAtSignal = sig.timestamp.includes("03-01T10") ? 142.50
      : sig.timestamp.includes("03-02T14") ? 148.50
      : sig.timestamp.includes("03-03T10") ? 145.00
      : 142.50;

    const priceChange4h = (Math.random() - 0.4) * 5; // slight bullish bias
    const correct4h = (sig.name.includes("whale") || sig.name.includes("tvl"))
      ? Math.random() > 0.25 // on-chain signals: ~75% hit rate
      : Math.random() > 0.45; // other signals: ~55% hit rate

    outcomes.push({
      signalId: sig.id,
      timeframe: "4h",
      priceAtSignal,
      priceAtEval: priceAtSignal * (1 + priceChange4h / 100),
      priceChangePct: priceChange4h,
      directionCorrect: correct4h,
      evaluatedAt: "2026-03-03T12:00:00Z",
    });
  }

  for (const o of outcomes) {
    await sql`INSERT INTO signal_outcomes (signal_id, timeframe, price_at_signal, price_at_eval, price_change_pct, direction_correct, evaluated_at)
      VALUES (${o.signalId}, ${o.timeframe}, ${o.priceAtSignal}, ${o.priceAtEval}, ${o.priceChangePct}, ${o.directionCorrect}, ${o.evaluatedAt})`;
  }
  console.log(`  Inserted ${outcomes.length} signal outcomes`);

  console.log("Done!");
}

seed().catch(console.error);
