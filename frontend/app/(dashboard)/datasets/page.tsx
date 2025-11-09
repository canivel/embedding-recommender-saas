'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { datasetApi } from '@/lib/api/datasets';
import { Dataset } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, Plus, Database, Calendar, TrendingUp } from 'lucide-react';

export default function DatasetsPage() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadDatasets();
  }, []);

  async function loadDatasets() {
    try {
      setLoading(true);
      const response = await datasetApi.listDatasets();
      setDatasets(response.datasets);
      setTotal(response.total);
    } catch (error: any) {
      toast.error('Failed to load datasets', {
        description: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  }

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  function formatNumber(num: number) {
    return new Intl.NumberFormat('en-US').format(num);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Datasets</h1>
          <p className="text-gray-600 mt-1">
            Manage your event datasets and configure column mappings
          </p>
        </div>
        <Button onClick={() => router.push('/datasets/new')}>
          <Plus className="w-4 h-4 mr-2" />
          New Dataset
        </Button>
      </div>

      {/* Stats */}
      {datasets.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Datasets</p>
                  <p className="text-2xl font-bold">{total}</p>
                </div>
                <Database className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Events</p>
                  <p className="text-2xl font-bold">
                    {formatNumber(
                      datasets.reduce((sum, d) => sum + d.total_events, 0)
                    )}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Uploads</p>
                  <p className="text-2xl font-bold">
                    {formatNumber(
                      datasets.reduce((sum, d) => sum + d.upload_count, 0)
                    )}
                  </p>
                </div>
                <Calendar className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Datasets List */}
      {datasets.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Database className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold mb-2">No datasets yet</h3>
              <p className="text-gray-600 mb-6">
                Create your first dataset to start uploading event data
              </p>
              <Button onClick={() => router.push('/datasets/new')}>
                <Plus className="w-4 h-4 mr-2" />
                Create Dataset
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {datasets.map((dataset) => (
            <Card
              key={dataset.id}
              className="hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => router.push(`/datasets/${dataset.id}`)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-xl">{dataset.name}</CardTitle>
                    {dataset.description && (
                      <CardDescription className="mt-2">
                        {dataset.description}
                      </CardDescription>
                    )}
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      dataset.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : dataset.status === 'processing'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {dataset.status}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Events</p>
                    <p className="font-semibold">
                      {formatNumber(dataset.total_events)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Sessions</p>
                    <p className="font-semibold">
                      {formatNumber(dataset.total_sessions)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Users</p>
                    <p className="font-semibold">
                      {formatNumber(dataset.unique_users)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Items</p>
                    <p className="font-semibold">
                      {formatNumber(dataset.unique_items)}
                    </p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t flex items-center justify-between text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Column Mapping:</span> {dataset.column_mapping.user_column} → {dataset.column_mapping.item_column} → {dataset.column_mapping.timestamp_column}
                  </div>
                  <div>
                    Updated {formatDate(dataset.updated_at)}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
