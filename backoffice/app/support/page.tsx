'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { useUIStore, useImpersonationStore } from '@/lib/store';
import { TenantHealthScore } from '@/lib/types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { AlertCircle, CheckCircle, User, Eye } from 'lucide-react';

// Mock tenant health scores
const mockHealthScores: TenantHealthScore[] = [
  {
    tenant_id: 'tenant-001',
    tenant_name: 'Acme Corp',
    score: 92,
    last_24h_errors: 2,
    last_24h_api_calls: 1500000,
    avg_latency_ms: 45,
    status: 'active',
  },
  {
    tenant_id: 'tenant-002',
    tenant_name: 'TechStart Inc',
    score: 78,
    last_24h_errors: 45,
    last_24h_api_calls: 450000,
    avg_latency_ms: 120,
    status: 'active',
  },
  {
    tenant_id: 'tenant-003',
    tenant_name: 'DataCorp',
    score: 65,
    last_24h_errors: 125,
    last_24h_api_calls: 300000,
    avg_latency_ms: 250,
    status: 'active',
  },
  {
    tenant_id: 'tenant-004',
    tenant_name: 'CloudWorks',
    score: 88,
    last_24h_errors: 8,
    last_24h_api_calls: 800000,
    avg_latency_ms: 75,
    status: 'active',
  },
  {
    tenant_id: 'tenant-005',
    tenant_name: 'Analytics Pro',
    score: 82,
    last_24h_errors: 15,
    last_24h_api_calls: 600000,
    avg_latency_ms: 95,
    status: 'active',
  },
];

export default function SupportDashboardPage() {
  const { addNotification } = useUIStore();
  const { setImpersonation } = useImpersonationStore();
  const [healthScores, setHealthScores] = useState<TenantHealthScore[]>([]);
  const [impersonateModalOpen, setImpersonateModalOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<TenantHealthScore | null>(null);
  const [impersonateReason, setImpersonateReason] = useState('');

  useEffect(() => {
    setHealthScores(mockHealthScores);
  }, []);

  const handleImpersonate = () => {
    if (selectedTenant) {
      setImpersonation(selectedTenant.tenant_id, selectedTenant.tenant_name);
      addNotification('warning', `Now impersonating ${selectedTenant.tenant_name}`);
      setImpersonateModalOpen(false);
      setImpersonateReason('');
    }
  };

  const openImpersonateModal = (tenant: TenantHealthScore) => {
    setSelectedTenant(tenant);
    setImpersonateModalOpen(true);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  const sortedTenants = [...healthScores].sort((a, b) => a.score - b.score);
  const criticalTenants = sortedTenants.filter((t) => t.score < 60);
  const warningTenants = sortedTenants.filter((t) => t.score >= 60 && t.score < 80);
  const healthyTenants = sortedTenants.filter((t) => t.score >= 80);

  const scatterData = healthScores.map((tenant) => ({
    x: tenant.last_24h_errors,
    y: tenant.avg_latency_ms,
    name: tenant.tenant_name,
    score: tenant.score,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Support Dashboard</h1>
        <p className="text-gray-600 mt-2">Monitor tenant health and debug issues</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardBody className="text-center">
            <CheckCircle className="w-8 h-8 text-green-600 mx-auto" />
            <p className="text-gray-500 text-sm font-medium mt-2">Healthy Tenants</p>
            <p className="text-4xl font-bold text-green-600 mt-2">{healthyTenants.length}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <AlertCircle className="w-8 h-8 text-yellow-600 mx-auto" />
            <p className="text-gray-500 text-sm font-medium mt-2">Warning</p>
            <p className="text-4xl font-bold text-yellow-600 mt-2">{warningTenants.length}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
            <p className="text-gray-500 text-sm font-medium mt-2">Critical</p>
            <p className="text-4xl font-bold text-red-600 mt-2">{criticalTenants.length}</p>
          </CardBody>
        </Card>
      </div>

      {/* Health Scores Chart */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Tenant Health Scores</h2>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={sortedTenants}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tenant_name" angle={-45} textAnchor="end" height={100} />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => `${value}/100`} />
              <Legend />
              <Bar dataKey="score" fill="#3b82f6" name="Health Score" />
            </BarChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      {/* Error vs Latency Scatter Plot */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Errors vs Latency (Last 24h)</h2>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" name="Errors" />
              <YAxis dataKey="y" name="Latency (ms)" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ active, payload }) => {
                if (active && payload && payload[0]) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-2 border border-gray-300 rounded shadow-lg">
                      <p className="font-semibold">{data.name}</p>
                      <p className="text-sm">Errors: {data.x}</p>
                      <p className="text-sm">Latency: {data.y}ms</p>
                      <p className="text-sm">Score: {data.score}</p>
                    </div>
                  );
                }
                return null;
              }} />
              <Scatter name="Tenants" data={scatterData} fill="#8884d8" />
            </ScatterChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      {/* Critical Issues */}
      {criticalTenants.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-red-600">Critical Issues</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {criticalTenants.map((tenant) => (
                <div key={tenant.tenant_id} className="p-4 border-l-4 border-red-500 bg-red-50 rounded">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-gray-900">{tenant.tenant_name}</p>
                      <p className="text-sm text-gray-600 mt-1">
                        Errors: {tenant.last_24h_errors} | Latency: {tenant.avg_latency_ms}ms avg
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getScoreColor(tenant.score)}`}>
                        {tenant.score}
                      </p>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => openImpersonateModal(tenant)}
                        className="mt-2"
                      >
                        <Eye size={16} className="mr-1" />
                        Investigate
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* All Tenants */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">All Tenants ({healthScores.length})</h2>
        </CardHeader>
        <CardBody>
          <div className="space-y-2">
            {sortedTenants.map((tenant) => (
              <div
                key={tenant.tenant_id}
                className={`p-4 rounded-lg border border-gray-200 ${getScoreBg(tenant.score)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{tenant.tenant_name}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Errors: {tenant.last_24h_errors} | Latency: {tenant.avg_latency_ms}ms | Calls: {(
                        tenant.last_24h_api_calls / 1000000
                      ).toFixed(1)}M
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getScoreColor(tenant.score)}`}>
                        {tenant.score}
                      </p>
                      <p className="text-xs text-gray-500">/100</p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openImpersonateModal(tenant)}
                    >
                      <Eye size={16} />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* Impersonate Modal */}
      <Modal
        isOpen={impersonateModalOpen}
        onClose={() => setImpersonateModalOpen(false)}
        title={`Impersonate ${selectedTenant?.tenant_name}`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setImpersonateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleImpersonate}>
              Start Impersonation
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason for Impersonation
            </label>
            <textarea
              value={impersonateReason}
              onChange={(e) => setImpersonateReason(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Debug API issues, verify configuration, etc."
              rows={4}
            />
          </div>
          {selectedTenant && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                You will be able to see this tenant's data and operations as if you were logged in as them. All actions will be logged in the audit trail.
              </p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
