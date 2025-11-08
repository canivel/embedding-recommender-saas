'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Table } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { getApiKeys, createApiKey, revokeApiKey } from '@/lib/api/api-keys';
import { Plus, Key, Copy, Trash2, CheckCircle, XCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const createKeySchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
});

type CreateKeyFormData = z.infer<typeof createKeySchema>;

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: getApiKeys,
  });

  const createMutation = useMutation({
    mutationFn: createApiKey,
    onSuccess: (data) => {
      setNewApiKey(data.key);
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateKeyFormData>({
    resolver: zodResolver(createKeySchema),
  });

  const onSubmit = async (data: CreateKeyFormData) => {
    await createMutation.mutateAsync({
      name: data.name,
      permissions: ['read', 'write'],
    });
    reset();
  };

  const handleCopyKey = () => {
    if (newApiKey) {
      navigator.clipboard.writeText(newApiKey);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const handleCloseCreateModal = () => {
    setIsCreateModalOpen(false);
    setNewApiKey(null);
    setCopiedKey(false);
    reset();
  };

  const columns = [
    {
      header: 'Name',
      accessor: 'name' as const,
      render: (value: string) => (
        <div className="flex items-center gap-2">
          <Key className="h-4 w-4 text-gray-400" />
          <span className="font-medium">{value}</span>
        </div>
      ),
    },
    {
      header: 'Key Prefix',
      accessor: 'key_prefix' as const,
      render: (value: string) => (
        <code className="px-2 py-1 bg-gray-100 rounded text-sm">{value}...</code>
      ),
    },
    {
      header: 'Status',
      accessor: 'status' as const,
      render: (value: string) =>
        value === 'active' ? (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-600">
            <CheckCircle className="h-3 w-3" />
            Active
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-600">
            <XCircle className="h-3 w-3" />
            Revoked
          </span>
        ),
    },
    {
      header: 'Created',
      accessor: 'created_at' as const,
      render: (value: string) =>
        formatDistanceToNow(new Date(value), { addSuffix: true }),
    },
    {
      header: 'Last Used',
      accessor: 'last_used_at' as const,
      render: (value: string | null) =>
        value
          ? formatDistanceToNow(new Date(value), { addSuffix: true })
          : 'Never',
    },
    {
      header: 'Actions',
      accessor: 'id' as const,
      render: (value: string, row: any) =>
        row.status === 'active' ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (confirm('Are you sure you want to revoke this API key?')) {
                revokeMutation.mutate(value);
              }
            }}
            className="text-red-600 hover:text-red-700 border-red-300"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Revoke
          </Button>
        ) : (
          <span className="text-xs text-gray-400">Revoked</span>
        ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">API Keys</h1>
          <p className="text-gray-600 mt-1">
            Manage API keys for accessing your recommendation service
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => setIsCreateModalOpen(true)}
        >
          <Plus className="h-5 w-5 mr-2" />
          Create API Key
        </Button>
      </div>

      {/* API Keys Table */}
      <Card>
        {isLoading ? (
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        ) : apiKeys && apiKeys.keys.length > 0 ? (
          <Table columns={columns} data={apiKeys.keys} />
        ) : (
          <div className="text-center py-12">
            <Key className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-4">No API keys yet</p>
            <Button
              variant="primary"
              onClick={() => setIsCreateModalOpen(true)}
            >
              Create Your First API Key
            </Button>
          </div>
        )}
      </Card>

      {/* Create API Key Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={handleCloseCreateModal}
        title={newApiKey ? 'API Key Created' : 'Create New API Key'}
      >
        {newApiKey ? (
          <div className="space-y-4">
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm font-medium text-yellow-800 mb-2">
                Important: Copy this key now
              </p>
              <p className="text-xs text-yellow-700">
                You won't be able to see this key again after closing this dialog.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your API Key
              </label>
              <div className="flex gap-2">
                <Input
                  value={newApiKey}
                  readOnly
                  className="font-mono text-sm"
                />
                <Button
                  variant={copiedKey ? 'primary' : 'outline'}
                  onClick={handleCopyKey}
                >
                  {copiedKey ? (
                    <>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleCloseCreateModal}
              className="w-full"
            >
              Done
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Key Name
              </label>
              <Input
                placeholder="Production API Key"
                {...register('name')}
                error={errors.name?.message}
              />
              <p className="text-xs text-gray-500 mt-1">
                Choose a descriptive name to identify this key
              </p>
            </div>

            <div className="flex gap-3">
              <Button
                type="submit"
                variant="primary"
                disabled={createMutation.isPending}
                className="flex-1"
              >
                {createMutation.isPending ? 'Creating...' : 'Create Key'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleCloseCreateModal}
              >
                Cancel
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
