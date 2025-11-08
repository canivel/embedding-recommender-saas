'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { StatusBadge, Badge } from '@/components/ui/Badge';
import { ServiceHealth, SystemHealth } from '@/lib/types';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react';

// Mock system health data
const mockSystemHealth: SystemHealth = {
  status: 'healthy',
  services: [
    {
      name: 'Backend API',
      status: 'healthy',
      uptime_percent: 99.98,
      latency_ms: 45,
      last_check: new Date().toISOString(),
    },
    {
      name: 'ML Engine',
      status: 'healthy',
      uptime_percent: 99.95,
      latency_ms: 120,
      last_check: new Date().toISOString(),
    },
    {
      name: 'PostgreSQL',
      status: 'healthy',
      uptime_percent: 100,
      latency_ms: 15,
      last_check: new Date().toISOString(),
    },
    {
      name: 'Redis',
      status: 'degraded',
      uptime_percent: 99.5,
      latency_ms: 250,
      last_check: new Date().toISOString(),
    },
    {
      name: 'S3 Storage',
      status: 'healthy',
      uptime_percent: 99.99,
      latency_ms: 80,
      last_check: new Date().toISOString(),
    },
  ],
  timestamp: new Date().toISOString(),
};

const performanceData = [
  { time: '00:00', latency: 45, throughput: 1200, errors: 2 },
  { time: '01:00', latency: 48, throughput: 1350, errors: 3 },
  { time: '02:00', latency: 42, throughput: 980, errors: 1 },
  { time: '03:00', latency: 50, throughput: 1450, errors: 4 },
  { time: '04:00', latency: 45, throughput: 1200, errors: 2 },
  { time: '05:00', latency: 52, throughput: 1500, errors: 5 },
  { time: '06:00', latency: 48, throughput: 1300, errors: 2 },
];

const cpuData = [
  { time: '00:00', cpu: 35 },
  { time: '01:00', cpu: 42 },
  { time: '02:00', cpu: 28 },
  { time: '03:00', cpu: 48 },
  { time: '04:00', cpu: 35 },
  { time: '05:00', cpu: 55 },
  { time: '06:00', cpu: 40 },
];

const statusIconMap = {
  healthy: <CheckCircle className="w-5 h-5 text-green-600" />,
  degraded: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
  unhealthy: <AlertCircle className="w-5 h-5 text-red-600" />,
};

export default function MonitoringPage() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth>(mockSystemHealth);

  useEffect(() => {
    // In a real app, fetch system health data
    setSystemHealth(mockSystemHealth);
  }, []);

  const healthyServices = systemHealth.services.filter((s) => s.status === 'healthy').length;
  const degradedServices = systemHealth.services.filter((s) => s.status === 'degraded').length;
  const unhealthyServices = systemHealth.services.filter((s) => s.status === 'unhealthy').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">System Monitoring</h1>
        <p className="text-gray-600 mt-2">Real-time system health and performance metrics</p>
      </div>

      {/* System Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Overall Status</p>
            <div className="flex items-center justify-center gap-2 mt-2">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <p className="text-2xl font-bold text-green-600">Healthy</p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Services</p>
            <p className="text-4xl font-bold text-green-600 mt-2">{healthyServices}</p>
            <p className="text-xs text-gray-600 mt-2">
              {degradedServices} degraded, {unhealthyServices} down
            </p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Avg Latency</p>
            <p className="text-4xl font-bold text-blue-600 mt-2">52ms</p>
            <p className="text-xs text-gray-600 mt-2">P95: 120ms</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Uptime</p>
            <p className="text-4xl font-bold text-green-600 mt-2">99.98%</p>
            <p className="text-xs text-gray-600 mt-2">Last 30 days</p>
          </CardBody>
        </Card>
      </div>

      {/* Service Health Status */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Service Health</h2>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {systemHealth.services.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-4">
                  {statusIconMap[service.status]}
                  <div>
                    <p className="font-semibold text-gray-900">{service.name}</p>
                    <p className="text-sm text-gray-600">
                      Uptime: {service.uptime_percent.toFixed(2)}% | Latency: {service.latency_ms}ms
                    </p>
                  </div>
                </div>
                <StatusBadge status={service.status} />
              </div>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Latency (Last 6 Hours)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip formatter={(value) => `${value}ms`} />
                <Legend />
                <Line type="monotone" dataKey="latency" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Error Rate (Last 6 Hours)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="errors" fill="#fecaca" stroke="#ef4444" />
              </AreaChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Throughput (Last 6 Hours)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip formatter={(value) => `${value} req/s`} />
                <Legend />
                <Line type="monotone" dataKey="throughput" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">CPU Usage (Last 6 Hours)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={cpuData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => `${value}%`} />
                <Legend />
                <Area type="monotone" dataKey="cpu" fill="#bfdbfe" stroke="#3b82f6" />
              </AreaChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      {/* Grafana Embed Notice */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Advanced Dashboards</h2>
        </CardHeader>
        <CardBody>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <p className="text-blue-900">
              For detailed metrics and custom dashboards, visit{' '}
              <a href="#" className="font-semibold underline">
                Grafana Dashboard
              </a>
              . Embedded Grafana dashboards can be integrated here in production.
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
