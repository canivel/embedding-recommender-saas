'use client';

import { Card } from '@/components/ui/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { UsageChartData } from '@/types';

interface UsageChartProps {
  data?: UsageChartData[];
  isLoading: boolean;
}

export function UsageChart({ data, isLoading }: UsageChartProps) {
  if (isLoading) {
    return (
      <Card>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-80 bg-gray-100 rounded"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">API Usage</h3>
        <p className="text-sm text-gray-600">Last 30 days activity</p>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data || []}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="api_calls"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
            name="API Calls"
          />
          <Line
            type="monotone"
            dataKey="recommendations"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={{ fill: '#8b5cf6', r: 4 }}
            activeDot={{ r: 6 }}
            name="Recommendations"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
