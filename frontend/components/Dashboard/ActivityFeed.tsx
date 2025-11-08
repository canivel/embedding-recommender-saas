'use client';

import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { getActivityFeed } from '@/lib/api/dashboard';
import { Upload, Key, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ActivityItem } from '@/types';

export function ActivityFeed() {
  const { data: activities, isLoading } = useQuery({
    queryKey: ['activity-feed'],
    queryFn: getActivityFeed,
  });

  const getIcon = (type: string) => {
    switch (type) {
      case 'upload':
        return Upload;
      case 'api_key_created':
        return Key;
      case 'model_update':
        return RefreshCw;
      default:
        return AlertCircle;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
          <p className="text-sm text-gray-600">Latest updates and events</p>
        </div>
        <button className="text-sm font-medium text-blue-600 hover:text-blue-700">
          View All
        </button>
      </div>

      <div className="space-y-4">
        {activities && activities.length > 0 ? (
          activities.map((activity: ActivityItem) => {
            const Icon = getIcon(activity.type);
            const statusColor = getStatusColor(activity.status);

            return (
              <div key={activity.id} className="flex items-start gap-4">
                <div className={`p-2 rounded-full ${statusColor}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDistanceToNow(new Date(activity.timestamp), {
                      addSuffix: true,
                    })}
                  </p>
                </div>
                {activity.status === 'success' && (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                )}
              </div>
            );
          })
        ) : (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No recent activity</p>
          </div>
        )}
      </div>
    </Card>
  );
}
