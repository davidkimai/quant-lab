/**
 * EquityCurve component.
 * 
 * Visualizes portfolio value over time using Recharts line chart.
 * Shows real-time updates during backtest execution.
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DataPoint {
  date: string;
  value: number;
}

interface EquityCurveProps {
  data: DataPoint[];
  isRunning: boolean;
}

export default function EquityCurve({ data, isRunning }: EquityCurveProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Portfolio Value</h2>
        {isRunning && (
          <span className="flex items-center text-blue-600">
            <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Running...
          </span>
        )}
      </div>

      {data.length === 0 ? (
        <div className="flex items-center justify-center h-80 text-gray-400">
          <p>No data to display. Run a backtest to see results.</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={(value: number) => [`$${value.toFixed(2)}`, 'Portfolio Value']}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Portfolio Value"
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {data.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Starting Value</p>
            <p className="text-lg font-semibold">${data[0].value.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-500">Current Value</p>
            <p className="text-lg font-semibold">${data[data.length - 1].value.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-500">Change</p>
            <p className={`text-lg font-semibold ${
              data[data.length - 1].value >= data[0].value ? 'text-green-600' : 'text-red-600'
            }`}>
              {((data[data.length - 1].value - data[0].value) / data[0].value * 100).toFixed(2)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
