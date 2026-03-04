export interface Trade {
  id: number;
  timestamp: string;
  token: string;
  action: string;
  price: number | null;
  quantity: number | null;
  fee: number | null;
  portfolioSnapshot: string | null;
  brainDecision: string | null;
  regime: string | null;
  confidence: number | null;
}

export interface Reflection {
  id: number;
  timestamp: string;
  level: number;
  text: string;
  regime: string | null;
  performanceSummary: string | null;
}

export interface SignalRow {
  id: number;
  timestamp: string;
  token: string;
  name: string;
  source: string;
  direction: string;
  confidence: number;
  rawValue: number | null;
}

export interface SignalAccuracy {
  name: string;
  source: string;
  timeframe: string;
  total: number;
  correct: number;
  hitRate: number;
}

export interface OverviewData {
  latestTrade: Trade | null;
  portfolio: {
    cash: number;
    holdings: Record<string, number>;
    net_worth: number;
  } | null;
  recentTrades: Trade[];
  recentReflections: Reflection[];
  stats: {
    totalTrades: number;
    totalSignals: number;
    winRate: number;
    latestRegime: string;
  };
}
