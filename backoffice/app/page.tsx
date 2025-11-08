'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

export default function Home() {
  const router = useRouter();
  const { session } = useAuthStore();

  useEffect(() => {
    if (session) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [session, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-600">Redirecting...</p>
    </div>
  );
}
