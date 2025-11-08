'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { mockLogin } from '@/lib/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardBody } from '@/components/ui/Card';

const DEMO_CREDENTIALS = [
  { email: 'admin@acme.com', password: 'admin123', role: 'Super Admin' },
  { email: 'support@acme.com', password: 'support123', role: 'Support' },
  { email: 'dev@acme.com', password: 'dev123', role: 'Developer' },
];

export default function LoginPage() {
  const router = useRouter();
  const { setSession } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const session = await mockLogin(email, password);
      if (session) {
        setSession(session);
        router.push('/dashboard');
      } else {
        setError('Invalid email or password');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async (email: string, password: string) => {
    setLoading(true);
    setError('');
    try {
      const session = await mockLogin(email, password);
      if (session) {
        setSession(session);
        router.push('/dashboard');
      }
    } catch (err) {
      setError('Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Backoffice</h1>
          <p className="text-gray-600 mt-2">Admin Portal</p>
        </div>

        {/* Login Form */}
        <Card className="mb-6">
          <CardBody className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Input
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@acme.com"
                  disabled={loading}
                  required
                />
              </div>

              <div>
                <Input
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  required
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                fullWidth
                loading={loading}
                disabled={loading}
                className="w-full"
              >
                Sign In
              </Button>
            </form>
          </CardBody>
        </Card>

        {/* Demo Credentials */}
        <div className="space-y-2">
          <p className="text-sm text-gray-600 text-center font-semibold">Demo Accounts</p>
          {DEMO_CREDENTIALS.map((cred) => (
            <button
              key={cred.email}
              onClick={() => quickLogin(cred.email, cred.password)}
              disabled={loading}
              className="w-full p-3 text-left border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <p className="font-medium text-gray-900">{cred.role}</p>
              <p className="text-xs text-gray-500">{cred.email}</p>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="text-center mt-6 text-xs text-gray-500">
          <p>Mock SSO for Development</p>
          <p className="mt-1">All accounts use test credentials</p>
        </div>
      </div>
    </div>
  );
}
