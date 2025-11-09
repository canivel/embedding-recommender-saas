'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { datasetApi } from '@/lib/api/datasets';
import { DatasetCreate } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, ArrowLeft, Database } from 'lucide-react';

export default function NewDatasetPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<DatasetCreate>({
    name: '',
    description: '',
    column_mapping: {
      user_column: 'user_id',
      item_column: 'item_id',
      timestamp_column: 'timestamp',
      session_column: '',
      target_column: '',
    },
    session_config: {
      auto_detect: true,
      timeout_minutes: 30,
    },
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!formData.name) {
      toast.error('Please provide a dataset name');
      return;
    }

    if (
      !formData.column_mapping.user_column ||
      !formData.column_mapping.item_column ||
      !formData.column_mapping.timestamp_column
    ) {
      toast.error('Please provide all required column mappings');
      return;
    }

    try {
      setLoading(true);

      // Remove empty optional fields
      const cleanedData = {
        ...formData,
        column_mapping: {
          ...formData.column_mapping,
          session_column: formData.column_mapping.session_column || undefined,
          target_column: formData.column_mapping.target_column || undefined,
        },
      };

      const dataset = await datasetApi.createDataset(cleanedData);

      toast.success('Dataset created successfully');
      router.push(`/datasets/${dataset.id}`);
    } catch (error: any) {
      toast.error('Failed to create dataset', {
        description: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="icon"
          onClick={() => router.back()}
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Create New Dataset</h1>
          <p className="text-gray-600 mt-1">
            Configure your event data structure and column mappings
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>
              Provide a name and description for your dataset
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Dataset Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="E.g., E-commerce Events, Content Interactions"
                required
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Describe what events this dataset contains..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Column Mapping */}
        <Card>
          <CardHeader>
            <CardTitle>Column Mapping</CardTitle>
            <CardDescription>
              Map your CSV columns to semantic roles. Use the exact column names from your CSV files.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="user_column">User Column *</Label>
                <Input
                  id="user_column"
                  value={formData.column_mapping.user_column}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      column_mapping: {
                        ...formData.column_mapping,
                        user_column: e.target.value,
                      },
                    })
                  }
                  placeholder="customer_id, user_id, etc."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Column identifying the user
                </p>
              </div>

              <div>
                <Label htmlFor="item_column">Item Column *</Label>
                <Input
                  id="item_column"
                  value={formData.column_mapping.item_column}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      column_mapping: {
                        ...formData.column_mapping,
                        item_column: e.target.value,
                      },
                    })
                  }
                  placeholder="product_id, content_id, etc."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Column identifying the item
                </p>
              </div>

              <div>
                <Label htmlFor="timestamp_column">Timestamp Column *</Label>
                <Input
                  id="timestamp_column"
                  value={formData.column_mapping.timestamp_column}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      column_mapping: {
                        ...formData.column_mapping,
                        timestamp_column: e.target.value,
                      },
                    })
                  }
                  placeholder="event_time, timestamp, etc."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Column with event timestamp
                </p>
              </div>

              <div>
                <Label htmlFor="session_column">Session Column (Optional)</Label>
                <Input
                  id="session_column"
                  value={formData.column_mapping.session_column}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      column_mapping: {
                        ...formData.column_mapping,
                        session_column: e.target.value,
                      },
                    })
                  }
                  placeholder="session_id"
                />
                <p className="text-xs text-gray-500 mt-1">
                  If sessions are pre-computed
                </p>
              </div>

              <div>
                <Label htmlFor="target_column">Target Column (Optional)</Label>
                <Input
                  id="target_column"
                  value={formData.column_mapping.target_column}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      column_mapping: {
                        ...formData.column_mapping,
                        target_column: e.target.value,
                      },
                    })
                  }
                  placeholder="purchased, clicked, etc."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Column indicating target outcome
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Session Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Session Detection</CardTitle>
            <CardDescription>
              Configure automatic session detection based on user inactivity
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="auto_detect"
                checked={formData.session_config.auto_detect}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    session_config: {
                      ...formData.session_config,
                      auto_detect: e.target.checked,
                    },
                  })
                }
                className="w-4 h-4"
              />
              <Label htmlFor="auto_detect" className="font-normal">
                Automatically detect sessions
              </Label>
            </div>

            {formData.session_config.auto_detect && (
              <div>
                <Label htmlFor="timeout_minutes">
                  Session Timeout (minutes)
                </Label>
                <Input
                  id="timeout_minutes"
                  type="number"
                  min="1"
                  max="1440"
                  value={formData.session_config.timeout_minutes}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      session_config: {
                        ...formData.session_config,
                        timeout_minutes: parseInt(e.target.value) || 30,
                      },
                    })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  A new session starts after this many minutes of inactivity
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Example */}
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">Example CSV Format</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm bg-white p-4 rounded border overflow-x-auto">
{`${formData.column_mapping.user_column || 'user_id'},${formData.column_mapping.item_column || 'item_id'},${formData.column_mapping.timestamp_column || 'timestamp'}${formData.column_mapping.target_column ? `,${formData.column_mapping.target_column}` : ''}
CUST001,PROD001,2024-01-01 10:00:00${formData.column_mapping.target_column ? ',1' : ''}
CUST001,PROD002,2024-01-01 10:05:00${formData.column_mapping.target_column ? ',0' : ''}
CUST002,PROD001,2024-01-01 11:00:00${formData.column_mapping.target_column ? ',1' : ''}`}
            </pre>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            <Database className="w-4 h-4 mr-2" />
            Create Dataset
          </Button>
        </div>
      </form>
    </div>
  );
}
