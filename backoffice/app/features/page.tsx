'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { useUIStore } from '@/lib/store';
import { hasPermission } from '@/lib/auth';
import { useAuthStore } from '@/lib/store';
import { Flag, Plus, Search, Edit2, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';

interface FeatureFlag {
  id: string;
  name: string;
  key: string;
  description: string;
  enabled: boolean;
  rollout_percentage: number;
  target_tenants: string[];
  created_at: string;
  updated_at: string;
}

// Mock feature flags
const mockFeatureFlags: FeatureFlag[] = [
  {
    id: 'flag-001',
    name: 'Advanced Analytics',
    key: 'advanced_analytics',
    description: 'Enable advanced analytics dashboard for tenants',
    enabled: true,
    rollout_percentage: 100,
    target_tenants: [],
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-15T10:30:00Z',
  },
  {
    id: 'flag-002',
    name: 'Graph Neural Network Model',
    key: 'gnn_model',
    description: 'Enable GNN model for recommendations',
    enabled: true,
    rollout_percentage: 25,
    target_tenants: ['tenant-001'],
    created_at: '2025-01-10T00:00:00Z',
    updated_at: '2025-01-14T15:20:00Z',
  },
  {
    id: 'flag-003',
    name: 'Real-time Recommendations',
    key: 'realtime_recs',
    description: 'Enable real-time recommendation updates',
    enabled: false,
    rollout_percentage: 0,
    target_tenants: [],
    created_at: '2025-01-05T00:00:00Z',
    updated_at: '2025-01-12T09:15:00Z',
  },
  {
    id: 'flag-004',
    name: 'Multi-modal Embeddings',
    key: 'multimodal_embeddings',
    description: 'Support text + image embeddings',
    enabled: true,
    rollout_percentage: 50,
    target_tenants: ['tenant-001', 'tenant-002'],
    created_at: '2025-01-08T00:00:00Z',
    updated_at: '2025-01-13T11:45:00Z',
  },
];

export default function FeatureFlagsPage() {
  const { session } = useAuthStore();
  const { addNotification } = useUIStore();
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [filteredFlags, setFilteredFlags] = useState<FeatureFlag[]>([]);
  const [search, setSearch] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlag | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    key: '',
    description: '',
    enabled: true,
    rollout_percentage: 100,
    target_tenants: '',
  });

  const canManageFlags = session?.user.role && hasPermission(session.user.role, 'manage_feature_flags');

  useEffect(() => {
    setFlags(mockFeatureFlags);
  }, []);

  useEffect(() => {
    const filtered = flags.filter(
      (flag) =>
        flag.name.toLowerCase().includes(search.toLowerCase()) ||
        flag.key.toLowerCase().includes(search.toLowerCase()) ||
        flag.description.toLowerCase().includes(search.toLowerCase())
    );
    setFilteredFlags(filtered);
  }, [flags, search]);

  const handleCreateFlag = () => {
    const newFlag: FeatureFlag = {
      id: `flag-${Date.now()}`,
      name: formData.name,
      key: formData.key,
      description: formData.description,
      enabled: formData.enabled,
      rollout_percentage: formData.rollout_percentage,
      target_tenants: formData.target_tenants.split(',').map((t) => t.trim()).filter(Boolean),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setFlags([...flags, newFlag]);
    addNotification('success', `Feature flag "${formData.name}" created successfully`);
    setCreateModalOpen(false);
    resetForm();
  };

  const handleUpdateFlag = () => {
    if (selectedFlag) {
      const updatedFlags = flags.map((flag) =>
        flag.id === selectedFlag.id
          ? {
              ...flag,
              name: formData.name,
              description: formData.description,
              enabled: formData.enabled,
              rollout_percentage: formData.rollout_percentage,
              target_tenants: formData.target_tenants.split(',').map((t) => t.trim()).filter(Boolean),
              updated_at: new Date().toISOString(),
            }
          : flag
      );
      setFlags(updatedFlags);
      addNotification('success', `Feature flag "${formData.name}" updated successfully`);
      setEditModalOpen(false);
      setSelectedFlag(null);
      resetForm();
    }
  };

  const handleToggleFlag = (flag: FeatureFlag) => {
    const updatedFlags = flags.map((f) =>
      f.id === flag.id ? { ...f, enabled: !f.enabled, updated_at: new Date().toISOString() } : f
    );
    setFlags(updatedFlags);
    addNotification('success', `Feature flag "${flag.name}" ${!flag.enabled ? 'enabled' : 'disabled'}`);
  };

  const handleDeleteFlag = (flag: FeatureFlag) => {
    setFlags(flags.filter((f) => f.id !== flag.id));
    addNotification('warning', `Feature flag "${flag.name}" deleted`);
  };

  const openEditModal = (flag: FeatureFlag) => {
    setSelectedFlag(flag);
    setFormData({
      name: flag.name,
      key: flag.key,
      description: flag.description,
      enabled: flag.enabled,
      rollout_percentage: flag.rollout_percentage,
      target_tenants: flag.target_tenants.join(', '),
    });
    setEditModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      key: '',
      description: '',
      enabled: true,
      rollout_percentage: 100,
      target_tenants: '',
    });
  };

  const enabledFlags = flags.filter((f) => f.enabled).length;
  const gradualRollouts = flags.filter((f) => f.enabled && f.rollout_percentage < 100).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Feature Flags</h1>
          <p className="text-gray-600 mt-2">Manage feature rollouts and toggles</p>
        </div>
        {canManageFlags && (
          <Button variant="primary" onClick={() => setCreateModalOpen(true)}>
            <Plus size={18} className="mr-2" />
            New Flag
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Total Flags</p>
            <p className="text-4xl font-bold text-gray-900 mt-2">{flags.length}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Enabled</p>
            <p className="text-4xl font-bold text-green-600 mt-2">{enabledFlags}</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center">
            <p className="text-gray-500 text-sm font-medium">Gradual Rollouts</p>
            <p className="text-4xl font-bold text-blue-600 mt-2">{gradualRollouts}</p>
          </CardBody>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardBody>
          <Input
            icon={<Search size={18} />}
            placeholder="Search feature flags..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </CardBody>
      </Card>

      {/* Feature Flags Table */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">All Feature Flags ({filteredFlags.length})</h2>
        </CardHeader>
        <CardBody>
          {filteredFlags.length === 0 ? (
            <div className="text-center py-12">
              <Flag className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No feature flags found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableCell header>Name</TableCell>
                  <TableCell header>Key</TableCell>
                  <TableCell header>Status</TableCell>
                  <TableCell header>Rollout</TableCell>
                  <TableCell header>Target Tenants</TableCell>
                  <TableCell header align="right">Actions</TableCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredFlags.map((flag) => (
                  <TableRow key={flag.id}>
                    <TableCell>
                      <div>
                        <p className="font-semibold text-gray-900">{flag.name}</p>
                        <p className="text-xs text-gray-500">{flag.description}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded">{flag.key}</code>
                    </TableCell>
                    <TableCell>
                      {flag.enabled ? (
                        <Badge variant="success">Enabled</Badge>
                      ) : (
                        <Badge variant="error">Disabled</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${flag.rollout_percentage}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">{flag.rollout_percentage}%</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {flag.target_tenants.length > 0 ? (
                        <Badge variant="info">{flag.target_tenants.length} tenants</Badge>
                      ) : (
                        <span className="text-gray-500 text-sm">All tenants</span>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <div className="flex items-center justify-end gap-2">
                        {canManageFlags && (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleToggleFlag(flag)}
                              title={flag.enabled ? 'Disable' : 'Enable'}
                            >
                              {flag.enabled ? (
                                <ToggleRight size={16} className="text-green-600" />
                              ) : (
                                <ToggleLeft size={16} className="text-gray-400" />
                              )}
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => openEditModal(flag)}>
                              <Edit2 size={16} />
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => handleDeleteFlag(flag)}>
                              <Trash2 size={16} className="text-red-600" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardBody>
      </Card>

      {/* Create Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          resetForm();
        }}
        title="Create Feature Flag"
        footer={
          <>
            <Button variant="ghost" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateFlag}>
              Create
            </Button>
          </>
        }
      >
        <form className="space-y-4">
          <Input
            label="Flag Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Advanced Analytics"
            required
          />
          <Input
            label="Flag Key"
            value={formData.key}
            onChange={(e) => setFormData({ ...formData, key: e.target.value })}
            placeholder="e.g., advanced_analytics"
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Describe what this flag controls"
              rows={3}
            />
          </div>
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                className="rounded border-gray-300"
              />
              <span className="text-sm font-medium text-gray-700">Enabled by default</span>
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rollout Percentage: {formData.rollout_percentage}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={formData.rollout_percentage}
              onChange={(e) => setFormData({ ...formData, rollout_percentage: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>
          <Input
            label="Target Tenants (comma-separated IDs)"
            value={formData.target_tenants}
            onChange={(e) => setFormData({ ...formData, target_tenants: e.target.value })}
            placeholder="tenant-001, tenant-002"
          />
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => {
          setEditModalOpen(false);
          setSelectedFlag(null);
          resetForm();
        }}
        title="Edit Feature Flag"
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleUpdateFlag}>
              Update
            </Button>
          </>
        }
      >
        <form className="space-y-4">
          <Input
            label="Flag Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input label="Flag Key" value={formData.key} disabled className="bg-gray-100" />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                className="rounded border-gray-300"
              />
              <span className="text-sm font-medium text-gray-700">Enabled</span>
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rollout Percentage: {formData.rollout_percentage}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={formData.rollout_percentage}
              onChange={(e) => setFormData({ ...formData, rollout_percentage: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>
          <Input
            label="Target Tenants (comma-separated IDs)"
            value={formData.target_tenants}
            onChange={(e) => setFormData({ ...formData, target_tenants: e.target.value })}
            placeholder="tenant-001, tenant-002"
          />
        </form>
      </Modal>
    </div>
  );
}
