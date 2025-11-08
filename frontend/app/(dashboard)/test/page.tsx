'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { getRecommendations } from '@/lib/api/recommendations';
import { Search, Sparkles, TrendingUp } from 'lucide-react';
import { Recommendation } from '@/types';

export default function TestPage() {
  const [userId, setUserId] = useState('');
  const [count, setCount] = useState(10);
  const [category, setCategory] = useState('');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  const recommendMutation = useMutation({
    mutationFn: getRecommendations,
    onSuccess: (data) => {
      setRecommendations(data.recommendations);
    },
  });

  const handleTest = () => {
    recommendMutation.mutate({
      user_id: userId,
      count,
      filters: category ? { categories: [category] } : undefined,
    });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Test Recommendations</h1>
        <p className="text-gray-600 mt-1">
          Test your recommendation engine with different user IDs and filters
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-1">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Test Parameters
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  User ID
                </label>
                <Input
                  placeholder="user_123"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Results
                </label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={count}
                  onChange={(e) => setCount(parseInt(e.target.value))}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category Filter (Optional)
                </label>
                <Input
                  placeholder="electronics"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                />
              </div>

              <Button
                variant="primary"
                className="w-full"
                onClick={handleTest}
                disabled={!userId || recommendMutation.isPending}
              >
                {recommendMutation.isPending ? (
                  'Getting Recommendations...'
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Get Recommendations
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Info Card */}
          <Card className="mt-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">
              How it works
            </h4>
            <p className="text-xs text-gray-600">
              Enter a user ID to receive personalized recommendations. The system
              uses embeddings to find the most relevant items based on user behavior
              and item characteristics.
            </p>
          </Card>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">
                Recommendation Results
              </h3>
              {recommendMutation.data && (
                <div className="text-sm text-gray-600">
                  Latency: {recommendMutation.data.metadata.latency_ms}ms
                </div>
              )}
            </div>

            {recommendMutation.isPending ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center gap-4 p-4 border border-gray-200 rounded-lg">
                    <div className="w-12 h-12 bg-gray-200 rounded"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : recommendations.length > 0 ? (
              <div className="space-y-3">
                {recommendations.map((rec, idx) => (
                  <div
                    key={rec.item_id}
                    className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  >
                    <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 text-white font-bold text-lg rounded-lg">
                      #{idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-gray-900">{rec.item_id}</p>
                      </div>
                      <div className="flex items-center gap-4 mt-1">
                        <div className="flex items-center gap-1 text-sm text-gray-600">
                          <TrendingUp className="h-4 w-4" />
                          Score: {(rec.score * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${rec.score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Search className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">
                  Enter a user ID and click "Get Recommendations" to see results
                </p>
              </div>
            )}

            {recommendMutation.isError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">
                  Failed to get recommendations. Please check the user ID and try again.
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
