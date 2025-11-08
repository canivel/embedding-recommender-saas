'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Calendar, Download, TrendingUp, Users, ShoppingBag, Eye } from 'lucide-react';
import { getAnalyticsData } from '@/lib/api/analytics';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('7d');

  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics', dateRange],
    queryFn: () => getAnalyticsData(dateRange),
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">
            Track your recommendation performance and user engagement
          </p>
        </div>
        <div className="flex gap-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Click-Through Rate</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">12.5%</p>
              <p className="text-xs text-green-600 mt-1">+2.3% vs last period</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Eye className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Conversion Rate</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">3.8%</p>
              <p className="text-xs text-green-600 mt-1">+0.5% vs last period</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <ShoppingBag className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Users</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">24.5K</p>
              <p className="text-xs text-green-600 mt-1">+15% vs last period</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Recommendations</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">8.2</p>
              <p className="text-xs text-gray-600 mt-1">per user session</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Over Time */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Performance Over Time
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={analytics?.performanceData || []}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="ctr"
                stroke="#3b82f6"
                name="CTR %"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="cvr"
                stroke="#8b5cf6"
                name="CVR %"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Top Recommended Items */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Recommended Items
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={analytics?.topItems || []}
              layout="horizontal"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="item" type="category" tick={{ fontSize: 12 }} width={100} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Interaction Types */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Interaction Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics?.interactionTypes || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {(analytics?.interactionTypes || []).map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* User Engagement */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            User Engagement Score
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics?.engagementData || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="engagement" fill="#10b981" name="Engagement Score" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Model Performance */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Model Performance Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600">Precision</p>
            <p className="text-3xl font-bold text-blue-600 mt-2">0.856</p>
            <p className="text-xs text-gray-600 mt-1">Last updated: 2 hours ago</p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-gray-600">Recall</p>
            <p className="text-3xl font-bold text-purple-600 mt-2">0.789</p>
            <p className="text-xs text-gray-600 mt-1">Last updated: 2 hours ago</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-gray-600">F1 Score</p>
            <p className="text-3xl font-bold text-green-600 mt-2">0.821</p>
            <p className="text-xs text-gray-600 mt-1">Last updated: 2 hours ago</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
