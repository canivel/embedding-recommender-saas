'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useForm } from 'react-hook-form';
import { getTenantInfo, updateTenantSettings } from '@/lib/api/tenant';
import { User, Building2, CreditCard, Bell, Save } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'profile' | 'company' | 'billing' | 'notifications'>('profile');
  const queryClient = useQueryClient();

  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: getTenantInfo,
  });

  const updateMutation = useMutation({
    mutationFn: updateTenantSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant'] });
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      name: tenant?.name || '',
      default_model: tenant?.settings?.default_model || 'two_tower',
      embedding_dimension: tenant?.settings?.embedding_dimension || 128,
    },
  });

  const onSubmit = async (data: any) => {
    await updateMutation.mutateAsync(data);
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'company', label: 'Company', icon: Building2 },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">
          Manage your account and application preferences
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-2">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </Card>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          {activeTab === 'profile' && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-6">
                Profile Settings
              </h3>
              <form className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      First Name
                    </label>
                    <Input placeholder="John" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Last Name
                    </label>
                    <Input placeholder="Doe" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <Input type="email" placeholder="john@example.com" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Zone
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option>UTC-08:00 Pacific Time</option>
                    <option>UTC-05:00 Eastern Time</option>
                    <option>UTC+00:00 UTC</option>
                  </select>
                </div>

                <Button variant="primary">
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </Button>
              </form>
            </Card>
          )}

          {activeTab === 'company' && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-6">
                Company Settings
              </h3>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company Name
                  </label>
                  <Input
                    {...register('name')}
                    placeholder="Acme Corp"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Model
                  </label>
                  <select
                    {...register('default_model')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="two_tower">Two Tower</option>
                    <option value="matrix_factorization">Matrix Factorization</option>
                    <option value="gnn">Graph Neural Network</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Embedding Dimension
                  </label>
                  <Input
                    type="number"
                    {...register('embedding_dimension')}
                    placeholder="128"
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  disabled={updateMutation.isPending}
                >
                  <Save className="h-4 w-4 mr-2" />
                  {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                </Button>
              </form>
            </Card>
          )}

          {activeTab === 'billing' && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-6">
                Billing & Subscription
              </h3>

              {/* Current Plan */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Current Plan</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1 capitalize">
                      {tenant?.plan || 'Starter'}
                    </p>
                  </div>
                  <Button variant="primary">Upgrade Plan</Button>
                </div>
              </div>

              {/* Usage */}
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">API Calls</span>
                    <span className="font-medium">750,000 / 1,000,000</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: '75%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Storage</span>
                    <span className="font-medium">3.2 GB / 10 GB</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '32%' }}></div>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-6">
                Notification Preferences
              </h3>

              <div className="space-y-4">
                {[
                  { label: 'Email notifications', description: 'Receive email updates about your account' },
                  { label: 'API usage alerts', description: 'Get notified when approaching limits' },
                  { label: 'Model training complete', description: 'Notify when model training finishes' },
                  { label: 'Weekly reports', description: 'Receive weekly analytics reports' },
                ].map((item) => (
                  <div key={item.label} className="flex items-start justify-between py-3 border-b border-gray-200">
                    <div>
                      <p className="font-medium text-gray-900">{item.label}</p>
                      <p className="text-sm text-gray-600">{item.description}</p>
                    </div>
                    <input
                      type="checkbox"
                      defaultChecked
                      className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
                    />
                  </div>
                ))}
              </div>

              <Button variant="primary" className="mt-6">
                <Save className="h-4 w-4 mr-2" />
                Save Preferences
              </Button>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
