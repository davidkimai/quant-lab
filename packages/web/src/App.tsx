/**
 * Main App component.
 * 
 * Orchestrates the entire UI:
 * - BacktestForm for user input
 * - EquityCurve for real-time visualization
 * - MetricsCard for performance results
 * - Progress tracking during backtest execution
 */

import { useState } from 'react';
import BacktestForm from './components/BacktestForm';
import EquityCurve from './components/EquityCurve';
import MetricsCard from './components/MetricsCard';
import { runBacktest } from './api/client';
import type { BacktestRequest, BacktestResults, ProgressEvent } from './types';

interface DataPoint {
  date: string;
  value: number;
}

export default function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [equityCurveData, setEquityCurveData] = useState<DataPoint[]>([]);
  const [results, setResults] = useState<BacktestResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBacktestSubmit = async (request: BacktestRequest) => {
    // Reset state
    setIsRunning(true);
    setProgress(0);
    setEquityCurveData([]);
    setResults(null);
    setError(null);

    try {
      await runBacktest(request, (event) => {
        if (event.type === 'progress') {
          const data = event.data as ProgressEvent;
          setProgress(data.progress * 100);
          
          // Update equity curve with new data point
          setEquityCurveData(prev => [
            ...prev,
            { date: data.date, value: data.portfolio_value }
          ]);
        } else if (event.type === 'complete') {
          setResults(event.data as BacktestResults);
          setProgress(100);
          setIsRunning(false);
        } else if (event.type === 'error') {
          setError(event.data as string);
          setIsRunning(false);
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Quant Lab
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Algorithmic Trading Backtesting Platform
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Progress Bar */}
        {isRunning && (
          <div className="mb-6 bg-white p-4 rounded-lg shadow-md">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Running Backtest
              </span>
              <span className="text-sm text-gray-500">
                {progress.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg
                className="h-5 w-5 text-red-400 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Form */}
          <div className="lg:col-span-1">
            <BacktestForm onSubmit={handleBacktestSubmit} isRunning={isRunning} />
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2 space-y-6">
            <EquityCurve data={equityCurveData} isRunning={isRunning} />
            <MetricsCard results={results} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            Quant Lab v0.1.0 - Open Source Algorithmic Trading Platform
          </p>
        </div>
      </footer>
    </div>
  );
}
