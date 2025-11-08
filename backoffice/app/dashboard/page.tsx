'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { mockAPI } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store';
import { Tenant, TenantHealthScore, SystemAlert } from '@/lib/types';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

export default function DashboardPage() {
  const { session } = useAuthStore();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setTenants(mockAPI.tenants);
        setAlerts(mockAPI.alerts);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const totalTenants = tenants.length;
  const activeTenants = tenants.filter((t) => t.status === 'active').length;
  const totalAPICallsUsed = tenants.reduce((sum, t) => sum + t.api_calls_used, 0);
  const totalAPICallsLimit = tenants.reduce((sum, t) => sum + t.api_calls_limit, 0);
  const utilizationPercent = Math.round((totalAPICallsUsed / totalAPICallsLimit) * 100);

  const chartData = [
    { date: 'Jan 1', calls: 1200000, errors: 1200 },
    { date: 'Jan 2', calls: 1300000, errors: 1300 },
    { date: 'Jan 3', calls: 1400000, errors: 900 },
    { date: 'Jan 4', calls: 1500000, errors: 1100 },
    { date: 'Jan 5', calls: 1450000, errors: 800 },
    { date: 'Jan 6', calls: 1600000, errors: 1400 },
    { date: 'Jan 7', calls: 1550000, errors: 1000 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome back, {session?.user.name}!</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Total Tenants</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">{totalTenants}</p>
            <p className="text-green-600 text-sm mt-2">{activeTenants} active</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">API Utilization</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">{utilizationPercent}%</p>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${utilizationPercent}%` }}
              />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">System Alerts</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">{alerts.length}</p>
            <p className="text-orange-600 text-sm mt-2">{alerts.filter((a) => a.severity === 'critical').length} critical</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Avg Health Score</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">85.3</p>
            <p className="text-green-600 text-sm mt-2">All systems nominal</p>
          </CardBody>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">API Calls (Last 7 Days)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => value.toLocaleString()} />
                <Legend />
                <Line type="monotone" dataKey="calls" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Error Rate (Last 7 Days)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => value.toLocaleString()} />
                <Legend />
                <Bar dataKey="errors" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      {/* System Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Active Alerts</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="p-4 border-l-4 border-orange-500 bg-orange-50 rounded">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-gray-900">{alert.title}</p>
                      <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                      {alert.service && (
                        <p className="text-xs text-gray-500 mt-2">Service: {alert.service}</p>
                      )}
                    </div>
                    <StatusBadge status={alert.severity} />
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Recent Tenants */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Recent Tenants</h2>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {tenants.slice(0, 5).map((tenant) => (
              <div key={tenant.id} className="p-4 border-b border-gray-200 last:border-b-0">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{tenant.name}</p>
                    <p className="text-sm text-gray-600">{tenant.contact_email}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <StatusBadge status={tenant.status} />
                      <Badge variant="info">{tenant.plan}</Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">
                      {Math.round((tenant.api_calls_used / tenant.api_calls_limit) * 100)}% used
                    </p>
                    <p className="text-xs text-gray-600">
                      {tenant.api_calls_used.toLocaleString()} / {tenant.api_calls_limit.toLocaleString()}
                    </p>
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
