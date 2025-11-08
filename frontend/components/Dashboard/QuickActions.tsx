'use client';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Upload, Key, FlaskConical, BookOpen } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function QuickActions() {
  const router = useRouter();

  const actions = [
    {
      title: 'Upload Data',
      description: 'Add items to your catalog',
      icon: Upload,
      color: 'blue',
      onClick: () => router.push('/data'),
    },
    {
      title: 'Create API Key',
      description: 'Generate a new key',
      icon: Key,
      color: 'purple',
      onClick: () => router.push('/api-keys'),
    },
    {
      title: 'Test Recommendations',
      description: 'Try the recommender',
      icon: FlaskConical,
      color: 'green',
      onClick: () => router.push('/test'),
    },
    {
      title: 'View Docs',
      description: 'Integration guides',
      icon: BookOpen,
      color: 'orange',
      onClick: () => router.push('/docs'),
    },
  ];

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>

      <div className="space-y-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.title}
              onClick={action.onClick}
              className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all group"
            >
              <div className={`p-2 rounded-lg bg-${action.color}-100 text-${action.color}-600 group-hover:bg-${action.color}-200`}>
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 text-left">
                <div className="text-sm font-medium text-gray-900">
                  {action.title}
                </div>
                <div className="text-xs text-gray-500">
                  {action.description}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </Card>
  );
}
