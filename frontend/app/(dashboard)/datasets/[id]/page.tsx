'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { datasetApi } from '@/lib/api/datasets';
import { Dataset, DatasetUpload, EventRecord, DatasetStatistics } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import {
  Loader2,
  ArrowLeft,
  Upload,
  Database,
  Users,
  Package,
  Activity,
  Calendar,
  RefreshCw,
  Download,
} from 'lucide-react';

export default function DatasetDetailPage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params.id as string;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [uploads, setUploads] = useState<DatasetUpload[]>([]);
  const [statistics, setStatistics] = useState<DatasetStatistics | null>(null);
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [eventsTotal, setEventsTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    loadDataset();
    loadUploads();
    loadStatistics();
    loadEvents();
  }, [datasetId]);

  async function loadDataset() {
    try {
      const data = await datasetApi.getDataset(datasetId);
      setDataset(data);
    } catch (error: any) {
      toast.error('Failed to load dataset', {
        description: error.response?.data?.detail || error.message,
      });
      router.push('/datasets');
    } finally {
      setLoading(false);
    }
  }

  async function loadUploads() {
    try {
      const response = await datasetApi.listUploads(datasetId, { limit: 10 });
      setUploads(response.uploads);
    } catch (error: any) {
      console.error('Failed to load uploads:', error);
    }
  }

  async function loadStatistics() {
    try {
      const stats = await datasetApi.getDatasetStatistics(datasetId);
      setStatistics(stats);
    } catch (error: any) {
      console.error('Failed to load statistics:', error);
    }
  }

  async function loadEvents(page = 0) {
    try {
      setEventsLoading(true);
      const response = await datasetApi.queryEvents(datasetId, {
        limit: pageSize,
        offset: page * pageSize,
      });
      setEvents(response.events);
      setEventsTotal(response.total);
      setCurrentPage(page);
    } catch (error: any) {
      console.error('Failed to load events:', error);
    } finally {
      setEventsLoading(false);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast.error('Please upload a CSV file');
      return;
    }

    try {
      setUploading(true);
      const upload = await datasetApi.uploadEvents(datasetId, file);

      toast.success('File uploaded successfully', {
        description: `Processed ${upload.accepted} events`,
      });

      // Refresh data
      loadDataset();
      loadUploads();
      loadStatistics();
      loadEvents();
    } catch (error: any) {
      toast.error('Failed to upload file', {
        description: error.response?.data?.detail || error.message,
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }

  function formatDate(date: string) {
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
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

  if (!dataset) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button variant="outline" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{dataset.name}</h1>
            {dataset.description && (
              <p className="text-gray-600 mt-1">{dataset.description}</p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Upload className="w-4 h-4 mr-2" />
            )}
            Upload CSV
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Events</p>
                <p className="text-2xl font-bold">
                  {formatNumber(dataset.total_events)}
                </p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Sessions</p>
                <p className="text-2xl font-bold">
                  {formatNumber(dataset.total_sessions)}
                </p>
              </div>
              <Database className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Unique Users</p>
                <p className="text-2xl font-bold">
                  {formatNumber(dataset.unique_users)}
                </p>
              </div>
              <Users className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Unique Items</p>
                <p className="text-2xl font-bold">
                  {formatNumber(dataset.unique_items)}
                </p>
              </div>
              <Package className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Column Mapping */}
      <Card>
        <CardHeader>
          <CardTitle>Column Mapping</CardTitle>
          <CardDescription>
            How CSV columns map to semantic roles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-600 font-medium">User Column</p>
              <p className="text-lg">{dataset.column_mapping.user_column}</p>
            </div>
            <div>
              <p className="text-gray-600 font-medium">Item Column</p>
              <p className="text-lg">{dataset.column_mapping.item_column}</p>
            </div>
            <div>
              <p className="text-gray-600 font-medium">Timestamp Column</p>
              <p className="text-lg">{dataset.column_mapping.timestamp_column}</p>
            </div>
            {dataset.column_mapping.session_column && (
              <div>
                <p className="text-gray-600 font-medium">Session Column</p>
                <p className="text-lg">{dataset.column_mapping.session_column}</p>
              </div>
            )}
            {dataset.column_mapping.target_column && (
              <div>
                <p className="text-gray-600 font-medium">Target Column</p>
                <p className="text-lg">{dataset.column_mapping.target_column}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Uploads */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Uploads</CardTitle>
              <CardDescription>Latest CSV file uploads</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadUploads}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {uploads.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Upload className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p>No uploads yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {uploads.map((upload) => (
                <div
                  key={upload.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex-1">
                    <p className="font-medium">{upload.filename}</p>
                    <p className="text-sm text-gray-600">
                      {formatNumber(upload.accepted)} events •{' '}
                      {formatDate(upload.uploaded_at)}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      upload.status === 'completed'
                        ? 'bg-green-100 text-green-800'
                        : upload.status === 'processing'
                        ? 'bg-blue-100 text-blue-800'
                        : upload.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {upload.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Events Explorer */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Events Data</CardTitle>
              <CardDescription>
                Showing {events.length} of {formatNumber(eventsTotal)} events
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => loadEvents(currentPage)}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {eventsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Database className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p>No events yet. Upload a CSV file to get started.</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b">
                    <tr className="text-left">
                      <th className="pb-2 font-medium">User ID</th>
                      <th className="pb-2 font-medium">Item ID</th>
                      <th className="pb-2 font-medium">Timestamp</th>
                      {events[0]?.session_id && (
                        <th className="pb-2 font-medium">Session ID</th>
                      )}
                      {events[0]?.target !== undefined && (
                        <th className="pb-2 font-medium">Target</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((event, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="py-2 font-mono text-xs">{event.user_id}</td>
                        <td className="py-2 font-mono text-xs">{event.item_id}</td>
                        <td className="py-2 text-xs">{formatDate(event.timestamp)}</td>
                        {event.session_id && (
                          <td className="py-2 font-mono text-xs">{event.session_id}</td>
                        )}
                        {event.target !== undefined && (
                          <td className="py-2">{String(event.target)}</td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {eventsTotal > pageSize && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-600">
                    Page {currentPage + 1} of {Math.ceil(eventsTotal / pageSize)}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadEvents(currentPage - 1)}
                      disabled={currentPage === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadEvents(currentPage + 1)}
                      disabled={(currentPage + 1) * pageSize >= eventsTotal}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
