import type { Metadata } from 'next';
import { MainLayout } from '@/components/Layout/MainLayout';
import './globals.css';

export const metadata: Metadata = {
  title: 'Backoffice Admin',
  description: 'Internal administration tools for the Embedding Recommender SaaS platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
}
