'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { Modal, ConfirmModal } from '@/components/ui/Modal';
import { StatusBadge, Badge } from '@/components/ui/Badge';
import { mockAPI } from '@/lib/api-client';
import { useFiltersStore, useUIStore } from '@/lib/store';
import { Tenant } from '@/lib/types';
import { Plus, Search, Edit2, Lock, Unlock } from 'lucide-react';

export default function TenantsPage() {
  const { tenantSearch, setTenantSearch } = useFiltersStore();
  const { addNotification } = useUIStore();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [filteredTenants, setFilteredTenants] = useState<Tenant[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'suspend' | 'activate' | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    contact_email: '',
    plan: 'starter' as const,
  });

  useEffect(() => {
    setTenants(mockAPI.tenants);
  }, []);

  useEffect(() => {
    const filtered = tenants.filter((tenant) =>
      tenant.name.toLowerCase().includes(tenantSearch.toLowerCase()) ||
      tenant.contact_email.toLowerCase().includes(tenantSearch.toLowerCase())
    );
    setFilteredTenants(filtered);
  }, [tenants, tenantSearch]);

  const handleCreateTenant = () => {
    addNotification('success', `Tenant "${formData.name}" created successfully`);
    setCreateModalOpen(false);
    setFormData({ name: '', contact_email: '', plan: 'starter' });
  };

  const handleUpdateTenant = () => {
    if (selectedTenant) {
      addNotification('success', `Tenant "${selectedTenant.name}" updated successfully`);
      setEditModalOpen(false);
      setSelectedTenant(null);
    }
  };

  const handleSuspendTenant = () => {
    if (selectedTenant) {
      addNotification('warning', `Tenant "${selectedTenant.name}" has been suspended`);
      setConfirmModalOpen(false);
      setConfirmAction(null);
    }
  };

  const openEditModal = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setFormData({
      name: tenant.name,
      contact_email: tenant.contact_email,
      plan: tenant.plan,
    });
    setEditModalOpen(true);
  };

  const openSuspendConfirm = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setConfirmAction('suspend');
    setConfirmModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tenant Management</h1>
          <p className="text-gray-600 mt-2">Manage all customer tenants</p>
        </div>
        <Button variant="primary" onClick={() => setCreateModalOpen(true)}>
          <Plus size={18} className="mr-2" />
          New Tenant
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardBody>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                icon={<Search size={18} />}
                placeholder="Search by name or email..."
                value={tenantSearch}
                onChange={(e) => setTenantSearch(e.target.value)}
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Tenants Table */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">
            All Tenants ({filteredTenants.length})
          </h2>
        </CardHeader>
        <CardBody>
          {filteredTenants.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No tenants found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableCell header>Name</TableCell>
                  <TableCell header>Contact</TableCell>
                  <TableCell header>Plan</TableCell>
                  <TableCell header>Status</TableCell>
                  <TableCell header align="right">API Usage</TableCell>
                  <TableCell header align="right">Actions</TableCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTenants.map((tenant) => (
                  <TableRow key={tenant.id}>
                    <TableCell>
                      <Link href={`/tenants/${tenant.id}`} className="text-blue-600 hover:underline">
                        {tenant.name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-gray-600">{tenant.contact_email}</TableCell>
                    <TableCell>
                      <Badge variant="info">{tenant.plan}</Badge>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={tenant.status} />
                    </TableCell>
                    <TableCell align="right" className="text-sm">
                      <div className="text-gray-900 font-semibold">
                        {Math.round((tenant.api_calls_used / tenant.api_calls_limit) * 100)}%
                      </div>
                      <div className="text-gray-500 text-xs">
                        {(tenant.api_calls_used / 1000000).toFixed(1)}M / {(tenant.api_calls_limit / 1000000).toFixed(0)}M
                      </div>
                    </TableCell>
                    <TableCell align="right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openEditModal(tenant)}
                        >
                          <Edit2 size={16} />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openSuspendConfirm(tenant)}
                        >
                          {tenant.status === 'active' ? (
                            <Lock size={16} />
                          ) : (
                            <Unlock size={16} />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardBody>
      </Card>

      {/* Create Tenant Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create New Tenant"
        footer={
          <>
            <Button variant="ghost" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateTenant}>
              Create
            </Button>
          </>
        }
      >
        <form className="space-y-4">
          <Input
            label="Tenant Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Acme Corp"
            required
          />
          <Input
            label="Contact Email"
            type="email"
            value={formData.contact_email}
            onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
            placeholder="admin@company.com"
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
            <select
              value={formData.plan}
              onChange={(e) => setFormData({ ...formData, plan: e.target.value as any })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="starter">Starter</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Edit Tenant Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Edit Tenant"
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleUpdateTenant}>
              Update
            </Button>
          </>
        }
      >
        <form className="space-y-4">
          <Input
            label="Tenant Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Contact Email"
            type="email"
            value={formData.contact_email}
            onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
            <select
              value={formData.plan}
              onChange={(e) => setFormData({ ...formData, plan: e.target.value as any })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="starter">Starter</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Confirm Modal */}
      <ConfirmModal
        isOpen={confirmModalOpen}
        onConfirm={handleSuspendTenant}
        onCancel={() => setConfirmModalOpen(false)}
        title={
          confirmAction === 'suspend'
            ? `Suspend ${selectedTenant?.name}?`
            : `Activate ${selectedTenant?.name}?`
        }
        message={
          confirmAction === 'suspend'
            ? 'This tenant will no longer be able to access the system. This action can be reversed.'
            : 'This tenant will regain access to the system.'
        }
        confirmText={confirmAction === 'suspend' ? 'Suspend' : 'Activate'}
        isDangerous={confirmAction === 'suspend'}
      />
    </div>
  );
}
