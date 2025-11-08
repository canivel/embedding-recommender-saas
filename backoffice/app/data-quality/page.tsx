'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { useUIStore } from '@/lib/store';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertTriangle, CheckCircle, AlertCircle, TrendingUp, Database, FileWarning } from 'lucide-react';
import { format } from 'date-fns';

interface ValidationError {
  id: string;
  tenant_id: string;
  tenant_name: string;
  error_type: string;
  field: string;
  message: string;
  count: number;
  first_seen: string;
  last_seen: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface DataFreshnessMetric {
  tenant_id: string;
  tenant_name: string;
  last_interaction_upload: string;
  last_item_upload: string;
  hours_since_last_upload: number;
  status: 'fresh' | 'stale' | 'critical';
}

interface AnomalyAlert {
  id: string;
  tenant_id: string;
  tenant_name: string;
  anomaly_type: string;
  description: string;
  detected_at: string;
  severity: 'low' | 'medium' | 'high';
  resolved: boolean;
}

// Mock data
const mockValidationErrors: ValidationError[] = [
  {
    id: 'err-001',
    tenant_id: 'tenant-001',
    tenant_name: 'Acme Corp',
    error_type: 'MISSING_FIELD',
    field: 'item_id',
    message: 'Required field missing',
    count: 125,
    first_seen: '2025-01-10T10:00:00Z',
    last_seen: '2025-01-15T14:30:00Z',
    severity: 'high',
  },
  {
    id: 'err-002',
    tenant_id: 'tenant-002',
    tenant_name: 'TechStart Inc',
    error_type: 'INVALID_FORMAT',
    field: 'timestamp',
    message: 'Invalid timestamp format',
    count: 45,
    first_seen: '2025-01-12T08:00:00Z',
    last_seen: '2025-01-15T12:00:00Z',
    severity: 'medium',
  },
  {
    id: 'err-003',
    tenant_id: 'tenant-001',
    tenant_name: 'Acme Corp',
    error_type: 'DUPLICATE_ITEM',
    field: 'item_id',
    message: 'Duplicate item ID detected',
    count: 8,
    first_seen: '2025-01-14T16:00:00Z',
    last_seen: '2025-01-15T11:00:00Z',
    severity: 'low',
  },
];

const mockFreshnessMetrics: DataFreshnessMetric[] = [
  {
    tenant_id: 'tenant-001',
    tenant_name: 'Acme Corp',
    last_interaction_upload: '2025-01-15T14:00:00Z',
    last_item_upload: '2025-01-15T13:30:00Z',
    hours_since_last_upload: 2,
    status: 'fresh',
  },
  {
    tenant_id: 'tenant-002',
    tenant_name: 'TechStart Inc',
    last_interaction_upload: '2025-01-14T10:00:00Z',
    last_item_upload: '2025-01-14T09:00:00Z',
    hours_since_last_upload: 30,
    status: 'stale',
  },
  {
    tenant_id: 'tenant-003',
    tenant_name: 'DataCorp',
    last_interaction_upload: '2025-01-12T08:00:00Z',
    last_item_upload: '2025-01-12T07:00:00Z',
    hours_since_last_upload: 78,
    status: 'critical',
  },
];

const mockAnomalies: AnomalyAlert[] = [
  {
    id: 'anom-001',
    tenant_id: 'tenant-002',
    tenant_name: 'TechStart Inc',
    anomaly_type: 'SUDDEN_TRAFFIC_SPIKE',
    description: 'API calls increased by 500% in last hour',
    detected_at: '2025-01-15T14:00:00Z',
    severity: 'high',
    resolved: false,
  },
  {
    id: 'anom-002',
    tenant_id: 'tenant-003',
    tenant_name: 'DataCorp',
    anomaly_type: 'DATA_QUALITY_DROP',
    description: 'Validation error rate increased to 15%',
    detected_at: '2025-01-15T12:30:00Z',
    severity: 'medium',
    resolved: false,
  },
];

const errorTrendData = [
  { date: 'Jan 9', errors: 120, validations: 50000 },
  { date: 'Jan 10', errors: 135, validations: 52000 },
  { date: 'Jan 11', errors: 110, validations: 48000 },
  { date: 'Jan 12', errors: 145, validations: 55000 },
  { date: 'Jan 13', errors: 125, validations: 51000 },
  { date: 'Jan 14', errors: 160, validations: 58000 },
  { date: 'Jan 15', errors: 178, validations: 60000 },
];

const errorTypeDistribution = [
  { type: 'Missing Field', count: 450 },
  { type: 'Invalid Format', count: 320 },
  { type: 'Duplicate', count: 180 },
  { type: 'Out of Range', count: 95 },
  { type: 'Type Mismatch', count: 65 },
];

export default function DataQualityPage() {
  const { addNotification } = useUIStore();
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [freshnessMetrics, setFreshnessMetrics] = useState<DataFreshnessMetric[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([]);

  useEffect(() => {
    setValidationErrors(mockValidationErrors);
    setFreshnessMetrics(mockFreshnessMetrics);
    setAnomalies(mockAnomalies);
  }, []);

  const handleResolveAnomaly = (anomalyId: string) => {
    setAnomalies(anomalies.map((a) => (a.id === anomalyId ? { ...a, resolved: true } : a)));
    addNotification('success', 'Anomaly marked as resolved');
  };

  const handleCleanupData = (tenantId: string) => {
    addNotification('success', 'Data cleanup job queued for processing');
  };

  const totalErrors = validationErrors.reduce((sum, err) => sum + err.count, 0);
  const criticalErrors = validationErrors.filter((err) => err.severity === 'critical').length;
  const freshData = freshnessMetrics.filter((m) => m.status === 'fresh').length;
  const staleData = freshnessMetrics.filter((m) => m.status === 'stale' || m.status === 'critical').length;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600';
      case 'high':
        return 'text-orange-600';
      case 'medium':
        return 'text-yellow-600';
      default:
        return 'text-blue-600';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'fresh':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'stale':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      default:
        return 'bg-red-50 text-red-700 border-red-200';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Data Quality</h1>
        <p className="text-gray-600 mt-2">Monitor data validation, freshness, and anomalies</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody className="text-center">
            <FileWarning className="w-8 h-8 text-orange-600 mx-auto" />
            <p className="text-gray-500 text-sm font-medium mt-2">Total Errors</p>
            <p className="text-4xl font-bold text-gray-900 mt-1">{totalErrors}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
            <p className="text-gray-500 text-sm font-medium mt-2">Critical Issues</p>
            <p className="text-4xl font-bold text-red-600 mt-1">{criticalErrors}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <CheckCircle className="w-8 h-8 text-green-600 mx-auto" />
            <p className="text-gray-500 text-sm font-medium mt-2">Fresh Data</p>
            <p className="text-4xl font-bold text-green-600 mt-1">{freshData}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <AlertTriangle className="w-8 h-8 text-yellow-600 mx-auto" />
            <p className="text-gray-500 text-sm font-medium mt-2">Stale Data</p>
            <p className="text-4xl font-bold text-yellow-600 mt-1">{staleData}</p>
          </CardBody>
        </Card>
      </div>

      {/* Active Anomalies */}
      {anomalies.filter((a) => !a.resolved).length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-red-600">Active Anomaly Alerts</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {anomalies
                .filter((a) => !a.resolved)
                .map((anomaly) => (
                  <div key={anomaly.id} className="p-4 border-l-4 border-red-500 bg-red-50 rounded">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-gray-900">{anomaly.tenant_name}</p>
                          <Badge variant="error">{anomaly.severity}</Badge>
                        </div>
                        <p className="text-sm text-gray-900 mt-1 font-medium">{anomaly.anomaly_type}</p>
                        <p className="text-sm text-gray-600 mt-1">{anomaly.description}</p>
                        <p className="text-xs text-gray-500 mt-2">
                          Detected: {format(new Date(anomaly.detected_at), 'MMM d, yyyy HH:mm')}
                        </p>
                      </div>
                      <Button size="sm" variant="primary" onClick={() => handleResolveAnomaly(anomaly.id)}>
                        Resolve
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Error Trends (Last 7 Days)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={errorTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="errors" stroke="#ef4444" strokeWidth={2} name="Errors" />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Error Type Distribution</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={errorTypeDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#f97316" name="Count" />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      {/* Validation Errors */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Validation Errors</h2>
        </CardHeader>
        <CardBody>
          <Table>
            <TableHeader>
              <TableRow>
                <TableCell header>Tenant</TableCell>
                <TableCell header>Error Type</TableCell>
                <TableCell header>Field</TableCell>
                <TableCell header>Message</TableCell>
                <TableCell header align="right">Count</TableCell>
                <TableCell header>Severity</TableCell>
                <TableCell header align="right">Actions</TableCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {validationErrors.map((error) => (
                <TableRow key={error.id}>
                  <TableCell>
                    <p className="font-semibold">{error.tenant_name}</p>
                    <p className="text-xs text-gray-500">{error.tenant_id}</p>
                  </TableCell>
                  <TableCell>
                    <Badge variant="info">{error.error_type}</Badge>
                  </TableCell>
                  <TableCell>
                    <code className="text-sm bg-gray-100 px-2 py-1 rounded">{error.field}</code>
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">{error.message}</TableCell>
                  <TableCell align="right" className="font-semibold">
                    {error.count.toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <span className={`text-sm font-medium ${getSeverityColor(error.severity)}`}>
                      {error.severity.toUpperCase()}
                    </span>
                  </TableCell>
                  <TableCell align="right">
                    <Button size="sm" variant="ghost" onClick={() => handleCleanupData(error.tenant_id)}>
                      Cleanup
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      {/* Data Freshness */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Data Freshness by Tenant</h2>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {freshnessMetrics.map((metric) => (
              <div
                key={metric.tenant_id}
                className={`p-4 rounded-lg border ${getStatusColor(metric.status)}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{metric.tenant_name}</p>
                    <div className="grid grid-cols-2 gap-4 mt-2">
                      <div>
                        <p className="text-xs text-gray-600">Last Interaction Upload</p>
                        <p className="text-sm font-medium">
                          {format(new Date(metric.last_interaction_upload), 'MMM d, HH:mm')}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Last Item Upload</p>
                        <p className="text-sm font-medium">
                          {format(new Date(metric.last_item_upload), 'MMM d, HH:mm')}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{metric.hours_since_last_upload}h</p>
                    <p className="text-xs text-gray-600">since last upload</p>
                    <Badge
                      variant={
                        metric.status === 'fresh' ? 'success' : metric.status === 'stale' ? 'warning' : 'error'
                      }
                      className="mt-2"
                    >
                      {metric.status.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
