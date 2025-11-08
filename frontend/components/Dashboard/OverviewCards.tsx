'use client';

import { Card } from '@/components/ui/Card';
import { TrendingUp, TrendingDown, Activity, Database, Zap, Clock } from 'lucide-react';
import { DashboardStats } from '@/types';

interface OverviewCardsProps {
  stats?: DashboardStats;
  isLoading: boolean;
}

export function OverviewCards({ stats, isLoading }: OverviewCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-32 bg-gray-200 rounded"></div>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'API Calls',
      value: stats?.total_api_calls?.toLocaleString() || '0',
      change: stats?.change_percentage?.api_calls || 0,
      icon: Activity,
      color: 'blue',
    },
    {
      title: 'Recommendations Served',
      value: stats?.total_recommendations?.toLocaleString() || '0',
      change: stats?.change_percentage?.recommendations || 0,
      icon: Zap,
      color: 'purple',
    },
    {
      title: 'Items Indexed',
      value: stats?.total_items?.toLocaleString() || '0',
      change: stats?.change_percentage?.items || 0,
      icon: Database,
      color: 'green',
    },
    {
      title: 'Avg Latency',
      value: `${stats?.avg_latency_ms || 0}ms`,
      change: 0,
      icon: Clock,
      color: 'orange',
    },
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-600',
      purple: 'bg-purple-100 text-purple-600',
      green: 'bg-green-100 text-green-600',
      orange: 'bg-orange-100 text-orange-600',
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => {
        const Icon = card.icon;
        const isPositive = card.change >= 0;

        return (
          <Card key={card.title} className="hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{card.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {card.value}
                </p>
                {card.change !== 0 && (
                  <div className="flex items-center gap-1 mt-2">
                    {isPositive ? (
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-600" />
                    )}
                    <span
                      className={`text-sm font-medium ${
                        isPositive ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {Math.abs(card.change)}%
                    </span>
                    <span className="text-sm text-gray-500">vs last period</span>
                  </div>
                )}
              </div>
              <div className={`p-3 rounded-lg ${getColorClasses(card.color)}`}>
                <Icon className="h-6 w-6" />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
