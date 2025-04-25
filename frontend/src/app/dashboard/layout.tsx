import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard | Sentinel AI',
  description: 'View recent analyses and monitor Solana blockchain security',
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
