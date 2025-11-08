'use client';

import React, { useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAuthStore } from '@/lib/store';
import { useRouter } from 'next/navigation';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const router = useRouter();
  const { isLoggedIn, initializeAuth } = useAuthStore();

  useEffect(() => {
    initializeAuth();
    if (!isLoggedIn) {
      router.push('/login');
    }
  }, [isLoggedIn, router, initializeAuth]);

  if (!isLoggedIn) {
    return null;
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <Header />

      <main className="flex-1 overflow-auto pt-16 lg:pt-0 pl-0 lg:pl-64">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
};
