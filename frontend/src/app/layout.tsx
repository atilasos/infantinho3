import type { Metadata } from 'next';
// Use system fonts in environments without Google Fonts access
import './globals.css';

import { QueryProvider } from '@/providers/query-provider';
import { AuthProvider } from '@/providers/auth-provider';

const geistSans = { variable: "--font-geist-sans" } as const;
const geistMono = { variable: "--font-geist-mono" } as const;

export const metadata: Metadata = {
  title: 'Infantinho 3.0',
  description: 'Portal cooperativo do Infantinho 3.0 (frontend headless).',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-slate-50 text-slate-900`}>
        <AuthProvider>
          <QueryProvider>{children}</QueryProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
