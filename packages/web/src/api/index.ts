/**
 * TypeScript types for API contracts.
 * 
 * Defines interfaces for backtest requests, responses, and streaming events.
 */

export interface Strategy {
  id: string;
  name: string;
  description: string;
}

export interface BacktestRequest {
  strategy_id: string;
  tickers: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
}

export interface BacktestResults {
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number;
  win_rate: number;
  num_trades: number;
}

export interface ProgressEvent {
  date: string;
  progress: number;
  portfolio_value: number;
}

export type BacktestEvent =
  | { type: 'progress'; data: ProgressEvent }
  | { type: 'complete'; data: BacktestResults }
  | { type: 'error'; data: string };
