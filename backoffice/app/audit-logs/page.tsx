'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { mockAPI } from '@/lib/api-client';
import { useFiltersStore, useUIStore } from '@/lib/store';
import { AuditLog } from '@/lib/types';
import { Download } from 'lucide-react';
import { format } from 'date-fns';

export default function AuditLogsPage() {
  const { auditLogSearch, auditLogActionFilter, setAuditLogSearch, setAuditLogActionFilter } =
    useFiltersStore();
  const { addNotification } = useUIStore();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    // Mock loading logs
    setLogs(mockAPI.auditLogs);
  }, []);

  useEffect(() => {
    let filtered = logs;

    // Search filter
    if (auditLogSearch) {
      filtered = filtered.filter(
        (log) =>
          log.user_email.toLowerCase().includes(auditLogSearch.toLowerCase()) ||
          log.action.toLowerCase().includes(auditLogSearch.toLowerCase()) ||
          log.resource_id.toLowerCase().includes(auditLogSearch.toLowerCase())
      );
    }

    // Action filter
    if (auditLogActionFilter) {
      filtered = filtered.filter((log) => log.action === auditLogActionFilter);
    }

    setFilteredLogs(filtered);
    setPage(1);
  }, [logs, auditLogSearch, auditLogActionFilter]);

  const paginatedLogs = filteredLogs.slice((page - 1) * pageSize, page * pageSize);
  const totalPages = Math.ceil(filteredLogs.length / pageSize);

  const handleExport = () => {
    const csv = [
      ['Timestamp', 'User', 'Action', 'Resource', 'Status', 'IP Address'],
      ...filteredLogs.map((log) => [
        log.timestamp,
        log.user_email,
        log.action,
        `${log.resource_type}:${log.resource_id}`,
        log.status,
        log.ip_address,
      ]),
    ]
      .map((row) => row.map((cell) => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString()}.csv`;
    a.click();
    addNotification('success', 'Audit logs exported successfully');
  };

  const uniqueActions = Array.from(new Set(logs.map((log) => log.action)));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600 mt-2">View all administrative actions and system events</p>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardBody className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by user, action, or resource..."
                value={auditLogSearch}
                onChange={(e) => setAuditLogSearch(e.target.value)}
              />
            </div>
            <select
              value={auditLogActionFilter || ''}
              onChange={(e) => setAuditLogActionFilter(e.target.value || null)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Actions</option>
              {uniqueActions.map((action) => (
                <option key={action} value={action}>
                  {action}
                </option>
              ))}
            </select>
            <Button variant="secondary" onClick={handleExport}>
              <Download size={18} className="mr-2" />
              Export CSV
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">
            Activity Log ({filteredLogs.length} events)
          </h2>
        </CardHeader>
        <CardBody>
          {paginatedLogs.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No audit logs found</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableCell header>Timestamp</TableCell>
                    <TableCell header>User</TableCell>
                    <TableCell header>Action</TableCell>
                    <TableCell header>Resource</TableCell>
                    <TableCell header>Status</TableCell>
                    <TableCell header align="right">IP Address</TableCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="text-sm">
                        {format(new Date(log.timestamp), 'MMM d, yyyy HH:mm:ss')}
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-semibold text-gray-900">{log.user_email}</p>
                          <p className="text-xs text-gray-500">{log.user_id}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="info">{log.action}</Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        <div>
                          <p className="font-semibold">{log.resource_type}</p>
                          <p className="text-xs text-gray-500">{log.resource_id}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={log.status} />
                      </TableCell>
                      <TableCell align="right" className="text-sm text-gray-600">
                        {log.ip_address}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, filteredLogs.length)} of{' '}
                  {filteredLogs.length} events
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                    const pageNum = i + 1;
                    return (
                      <Button
                        key={pageNum}
                        variant={page === pageNum ? 'primary' : 'ghost'}
                        size="sm"
                        onClick={() => setPage(pageNum)}
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={page === totalPages}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
