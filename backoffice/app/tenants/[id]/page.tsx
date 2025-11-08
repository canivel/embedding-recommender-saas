'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { useUIStore } from '@/lib/store';
import { TenantDetail, APIKey, ModelTrainingJob } from '@/lib/types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ArrowLeft, RotateCw, Trash2, Play, BarChart3 } from 'lucide-react';

// Mock tenant detail
const mockTenantDetail: TenantDetail = {
  id: 'tenant-001',
  name: 'Acme Corp',
  status: 'active',
  plan: 'enterprise',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-15T10:30:00Z',
  api_calls_limit: 10000000,
  api_calls_used: 7500000,
  contact_email: 'admin@acme.com',
  settings: {
    default_model: 'two_tower',
    embedding_dimension: 128,
    enable_analytics: true,
    retention_days: 90,
  },
  api_keys: [
    {
      id: 'key-001',
      name: 'Production Key',
      key_prefix: 'sk_live_abc123xyz',
      created_at: '2025-01-01T00:00:00Z',
      last_used_at: '2025-01-15T10:30:00Z',
      status: 'active',
      permissions: ['read', 'write'],
    },
  ],
  team_members: 5,
  last_activity: '2025-01-15T10:30:00Z',
  health_score: 92,
};

const mockTrainingJobs: ModelTrainingJob[] = [
  {
    id: 'job-001',
    tenant_id: 'tenant-001',
    model_type: 'two_tower',
    status: 'completed',
    progress_percent: 100,
    started_at: '2025-01-14T00:00:00Z',
    estimated_completion: '2025-01-14T04:00:00Z',
    completed_at: '2025-01-14T04:15:00Z',
  },
];

const usageData = [
  { date: 'Jan 9', calls: 1200000 },
  { date: 'Jan 10', calls: 1300000 },
  { date: 'Jan 11', calls: 1400000 },
  { date: 'Jan 12', calls: 1500000 },
  { date: 'Jan 13', calls: 1450000 },
  { date: 'Jan 14', calls: 1600000 },
  { date: 'Jan 15', calls: 1550000 },
];

export default function TenantDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { addNotification } = useUIStore();
  const [tenant, setTenant] = useState<TenantDetail>(mockTenantDetail);
  const [trainingModalOpen, setTrainingModalOpen] = useState(false);
  const [modelType, setModelType] = useState('two_tower');

  const handleTraining = () => {
    addNotification('success', 'Model training job triggered successfully');
    setTrainingModalOpen(false);
  };

  const handleRotateKey = (keyId: string) => {
    addNotification('success', 'API key rotated successfully');
  };

  const handleRevokeKey = (keyId: string) => {
    addNotification('warning', 'API key revoked successfully');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.back()}
        >
          <ArrowLeft size={18} />
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{tenant.name}</h1>
          <p className="text-gray-600 mt-1">{tenant.contact_email}</p>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody>
            <p className="text-gray-500 text-sm">Status</p>
            <StatusBadge status={tenant.status} className="mt-2" />
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <p className="text-gray-500 text-sm">Plan</p>
            <Badge variant="info" className="mt-2">{tenant.plan}</Badge>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <p className="text-gray-500 text-sm">Health Score</p>
            <p className="text-3xl font-bold text-green-600 mt-2">{tenant.health_score}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <p className="text-gray-500 text-sm">Team Members</p>
            <p className="text-3xl font-bold text-blue-600 mt-2">{tenant.team_members}</p>
          </CardBody>
        </Card>
      </div>

      {/* API Usage */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">API Usage</h2>
        </CardHeader>
        <CardBody>
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-900">Monthly Quota</span>
              <span className="text-gray-600">
                {Math.round((tenant.api_calls_used / tenant.api_calls_limit) * 100)}% used
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all"
                style={{
                  width: `${Math.round((tenant.api_calls_used / tenant.api_calls_limit) * 100)}%`,
                }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {(tenant.api_calls_used / 1000000).toFixed(1)}M / {(tenant.api_calls_limit / 1000000).toFixed(0)}M calls
            </p>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={usageData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => (value / 1000000).toFixed(1) + 'M'} />
              <Legend />
              <Line type="monotone" dataKey="calls" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">API Keys</h2>
        </CardHeader>
        <CardBody>
          <Table>
            <TableHeader>
              <TableRow>
                <TableCell header>Name</TableCell>
                <TableCell header>Key</TableCell>
                <TableCell header>Status</TableCell>
                <TableCell header>Created</TableCell>
                <TableCell header align="right">Actions</TableCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tenant.api_keys.map((key) => (
                <TableRow key={key.id}>
                  <TableCell className="font-semibold">{key.name}</TableCell>
                  <TableCell className="font-mono text-sm text-gray-600">{key.key_prefix}...</TableCell>
                  <TableCell>
                    <StatusBadge status={key.status} />
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {new Date(key.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRotateKey(key.id)}
                      >
                        <RotateCw size={16} />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRevokeKey(key.id)}
                      >
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      {/* Model Training */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Model Training</h2>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setTrainingModalOpen(true)}
          >
            <Play size={16} className="mr-2" />
            Trigger Training
          </Button>
        </CardHeader>
        <CardBody>
          {mockTrainingJobs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No training jobs yet</p>
          ) : (
            <div className="space-y-3">
              {mockTrainingJobs.map((job) => (
                <div key={job.id} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="font-semibold text-gray-900">{job.model_type}</p>
                      <p className="text-sm text-gray-600">Job ID: {job.id}</p>
                    </div>
                    <StatusBadge status={job.status} />
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full transition-all"
                      style={{ width: `${job.progress_percent}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{job.progress_percent}% complete</p>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Training Modal */}
      <Modal
        isOpen={trainingModalOpen}
        onClose={() => setTrainingModalOpen(false)}
        title="Trigger Model Training"
        footer={
          <>
            <Button variant="ghost" onClick={() => setTrainingModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleTraining}>
              Start Training
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Type
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="matrix_factorization">Matrix Factorization</option>
              <option value="two_tower">Two Tower (Default)</option>
              <option value="gnn">Graph Neural Network</option>
            </select>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              Training typically takes 2-4 hours depending on data size. The system will continue processing in the background.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
