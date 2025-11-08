'use client';

import { useQuery } from '@tanstack/react-query';
import { OverviewCards } from '@/components/Dashboard/OverviewCards';
import { UsageChart } from '@/components/Dashboard/UsageChart';
import { ActivityFeed } from '@/components/Dashboard/ActivityFeed';
import { QuickActions } from '@/components/Dashboard/QuickActions';
import { getDashboardStats, getUsageData } from '@/lib/api/dashboard';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
  });

  const { data: usageData, isLoading: usageLoading } = useQuery({
    queryKey: ['usage-data', 'last-30-days'],
    queryFn: () => getUsageData({ days: 30 }),
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Welcome back! Here's what's happening with your recommendations.
        </p>
      </div>

      {/* Overview Cards */}
      <OverviewCards stats={stats} isLoading={statsLoading} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Usage Chart - Takes 2 columns */}
        <div className="lg:col-span-2">
          <UsageChart data={usageData} isLoading={usageLoading} />
        </div>

        {/* Quick Actions */}
        <div>
          <QuickActions />
        </div>
      </div>

      {/* Activity Feed */}
      <ActivityFeed />
    </div>
  );
}
