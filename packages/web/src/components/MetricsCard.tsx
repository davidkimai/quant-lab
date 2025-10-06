/**
 * MetricsCard component.
 * 
 * Displays key performance metrics from backtest results.
 * Shows total return, Sharpe ratio, max drawdown, and trade statistics.
 */

import type { BacktestResults } from '../types';

interface MetricsCardProps {
  results: BacktestResults | null;
}

export default function MetricsCard({ results }: MetricsCardProps) {
  if (!results) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Performance Metrics</h2>
        <div className="flex items-center justify-center h-40 text-gray-400">
          <p>Run a backtest to see performance metrics.</p>
        </div>
      </div>
    );
  }

  const metrics = [
    {
      label: 'Total Return',
      value: `${results.total_return.toFixed(2)}%`,
      color: results.total_return >= 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      label: 'Final Value',
      value: `$${results.final_value.toLocaleString()}`,
      color: 'text-gray-900',
    },
    {
      label: 'Sharpe Ratio',
      value: results.sharpe_ratio?.toFixed(2) ?? 'N/A',
      color: 'text-gray-900',
    },
    {
      label: 'Sortino Ratio',
      value: results.sortino_ratio?.toFixed(2) ?? 'N/A',
      color: 'text-gray-900',
    },
    {
      label: 'Max Drawdown',
      value: `${results.max_drawdown.toFixed(2)}%`,
      color: 'text-red-600',
    },
    {
      label: 'Win Rate',
      value: `${results.win_rate.toFixed(1)}%`,
      color: 'text-gray-900',
    },
    {
      label: 'Total Trades',
      value: results.num_trades.toString(),
      color: 'text-gray-900',
    },
    {
      label: 'Strategy',
      value: results.strategy_name,
      color: 'text-gray-900',
    },
  ];

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Performance Metrics</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {metrics.map((metric) => (
          <div key={metric.label} className="space-y-1">
            <p className="text-sm text-gray-500">{metric.label}</p>
            <p className={`text-xl font-bold ${metric.color}`}>{metric.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Backtest Period</h3>
        <p className="text-sm text-gray-600">
          {new Date(results.start_date).toLocaleDateString()} to {new Date(results.end_date).toLocaleDateString()}
        </p>
      </div>

      {/* Key Insights */}
      <div className="mt-4 p-4 bg-blue-50 rounded-md">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Key Insights</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          {results.sharpe_ratio && results.sharpe_ratio > 1 && (
            <li>✓ Strong risk-adjusted returns (Sharpe {'>'}1)</li>
          )}
          {results.total_return > 0 && (
            <li>✓ Positive returns over backtest period</li>
          )}
          {Math.abs(results.max_drawdown) < 15 && (
            <li>✓ Well-controlled risk (Max Drawdown {'<'}15%)</li>
          )}
          {results.num_trades === 0 && (
            <li>⚠ No trades executed - consider adjusting strategy parameters</li>
          )}
        </ul>
      </div>
    </div>
  );
}
