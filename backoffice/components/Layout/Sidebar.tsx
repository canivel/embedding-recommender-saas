'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore, useUIStore, useImpersonationStore } from '@/lib/store';
import { canAccess } from '@/lib/auth';
import {
  LayoutDashboard,
  Users,
  FileText,
  Activity,
  Settings,
  BarChart3,
  LogOut,
  Menu,
  X,
  ShieldAlert,
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  permission: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: <LayoutDashboard size={20} />,
    permission: 'view_system_health',
  },
  {
    label: 'Tenants',
    href: '/tenants',
    icon: <Users size={20} />,
    permission: 'view_tenants',
  },
  {
    label: 'Audit Logs',
    href: '/audit-logs',
    icon: <FileText size={20} />,
    permission: 'view_audit_logs',
  },
  {
    label: 'System Monitoring',
    href: '/monitoring',
    icon: <BarChart3 size={20} />,
    permission: 'view_system_health',
  },
  {
    label: 'Support Dashboard',
    href: '/support',
    icon: <Activity size={20} />,
    permission: 'view_tenants',
  },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { session, logout } = useAuthStore();
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useUIStore();
  const { impersonatedTenantName, clearImpersonation } = useImpersonationStore();

  if (!session) return null;

  const isActive = (href: string) => pathname === href;

  return (
    <>
      {/* Mobile menu button */}
      <div className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between lg:hidden z-40">
        <h1 className="text-xl font-bold text-gray-900">Backoffice</h1>
        <button onClick={toggleSidebar} className="text-gray-600 hover:text-gray-900">
          {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`
          fixed left-0 top-0 h-screen bg-gray-900 text-white w-64 overflow-y-auto
          transition-transform duration-300 lg:translate-x-0 z-30
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Logo */}
        <div className="px-6 py-8 border-b border-gray-800">
          <h1 className="text-2xl font-bold">Backoffice</h1>
          <p className="text-gray-400 text-sm">Admin Portal</p>
        </div>

        {/* Impersonation Banner */}
        {impersonatedTenantName && (
          <div className="mx-4 mt-4 p-3 bg-yellow-900 rounded-lg border border-yellow-700">
            <div className="flex items-start gap-2">
              <ShieldAlert size={16} className="mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold">Impersonating</p>
                <p className="text-xs text-gray-300 truncate">{impersonatedTenantName}</p>
                <button
                  onClick={() => clearImpersonation()}
                  className="text-xs text-yellow-300 hover:text-yellow-200 mt-2 underline"
                >
                  Exit Impersonation
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="px-4 py-6 space-y-2">
          {NAV_ITEMS.map((item) => {
            if (!canAccess(session.user.role, item.permission)) {
              return null;
            }

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                  ${
                    isActive(item.href)
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800'
                  }
                `}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Section */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-gray-800 p-4 space-y-4">
          <div className="px-4 py-3 bg-gray-800 rounded-lg">
            <p className="text-xs text-gray-400">Logged in as</p>
            <p className="text-sm font-semibold truncate">{session.user.email}</p>
            <p className="text-xs text-gray-400 capitalize">{session.user.role.replace(/_/g, ' ')}</p>
          </div>

          <button
            onClick={() => {
              logout();
              window.location.href = '/login';
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors text-sm font-medium"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 lg:hidden z-20"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  );
};
