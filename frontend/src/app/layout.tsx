import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

import Navbar from '@/components/Navbar';
import SessionProvider from '@/components/SessionProvider';

import ConnectionIndicator from '@/components/ConnectionIndicator';
import { ClientThemeProvider } from '@/components/theme/ClientThemeProvider';
import { Toaster } from 'react-hot-toast';

// Configure the Inter font with default options only
const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Sentinel AI - Solana Blockchain Security Analysis',
  description: 'AI-powered security analysis for Solana blockchain addresses and tokens',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <SessionProvider>
          <ClientThemeProvider>
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
              <Navbar />
              <div className="fixed bottom-4 right-4 z-50">
                <ConnectionIndicator />
              </div>
              <main className="container py-6 mx-auto">
                {children}
              </main>
              <footer className="py-6 border-t border-gray-200 dark:border-gray-800">
                <div className="container mx-auto text-center text-sm text-gray-500 dark:text-gray-400">
                  © {new Date().getFullYear()} Sentinel AI. All rights reserved.
                </div>
              </footer>
              <Toaster />
            </div>
          </ClientThemeProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
