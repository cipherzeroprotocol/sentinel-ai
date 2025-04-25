import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import { Metadata, ResolvingMetadata } from 'next';
import { serverApi } from '@/lib/serverApi';
import { getServerSession } from 'next-auth/next'; 
import { authOptions } from '@/lib/auth';
import ReportContent from '@/components/reports/ReportContent';
import LoadingReport from '@/components/reports/LoadingReport';
import { AlertCircle } from 'lucide-react';

// Define params type for the page
interface ReportPageProps {
  params: {
    filename: string;
  };
  searchParams: { [key: string]: string | string[] | undefined };
}

// Generate metadata for the page
export async function generateMetadata(
  { params }: ReportPageProps,
  parent: ResolvingMetadata
): Promise<Metadata> {
  // Get the filename
  const { filename } = params;
  const decodedFilename = decodeURIComponent(filename);
  
  // Attempt to parse a meaningful title from the filename
  const reportTitle = decodedFilename
    .replace(/^report_/, '')
    .replace(/\.\w+$/, '')
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
    
  // Try to extract analysis type if possible
  let analysisType = "Security";
  const parts = decodedFilename.replace(/\.md$/, '').split('_');
  if (parts.length >= 4 && parts[0] === 'report') {
    analysisType = parts[1].charAt(0).toUpperCase() + parts[1].slice(1).replace(/-/g, ' ');
  }
  
  return {
    title: `${analysisType} Analysis Report | Sentinel AI`,
    description: `Security analysis report for ${reportTitle}`,
  };
}

// Server-side fetching of report data
async function fetchReportData(filename: string) {
  try {
    const decodedFilename = decodeURIComponent(filename);
    const content = await serverApi.getReportContent(decodedFilename);
    
    // Attempt to extract JSON data from markdown if present
    const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
    let analysisData = null;
    
    if (jsonMatch && jsonMatch[1]) {
      try {
        analysisData = JSON.parse(jsonMatch[1]);
      } catch (e) {
        console.error("Failed to parse embedded JSON data", e);
      }
    }
    
    return {
      content,
      analysisData,
    };
  } catch (error) {
    if ((error as any)?.statusCode === 404) {
      notFound();
    }
    throw error;
  }
}

// Main report page component - Server Component
export default async function ReportDetailPage({ params }: ReportPageProps) {
  const { filename } = params;
  const decodedFilename = decodeURIComponent(filename);
  
  // Verify user is authenticated
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    // This should be handled by middleware, but as an extra precaution
    return (
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-4 rounded-md">
        <p className="text-amber-700 dark:text-amber-300">
          You must be logged in to view this report.
        </p>
      </div>
    );
  }
  
  // Extract report information from filename
  const reportInfo = (() => {
    const parts = decodedFilename.replace(/\.md$/, '').split('_');
    if (parts.length >= 4 && parts[0] === 'report') {
      return {
        analysisType: parts[1].replace(/-/g, ' '),
        target: parts[2],
        timestamp: parts[3]
      };
    }
    return null;
  })();
  
  // Format report title for display
  const reportTitle = decodedFilename
    .replace(/^report_/, '')
    .replace(/\.\w+$/, '')
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6">
        <Link href="/reports" className="text-indigo-600 dark:text-indigo-400 hover:underline text-sm flex items-center">
          <span className="mr-1">←</span> Back to Reports List
        </Link>
      </div>

      <div className="mb-6">
        <h1 className="text-2xl lg:text-3xl font-bold mb-2 text-gray-800 dark:text-white break-words">
          {reportTitle}
        </h1>
        {reportInfo && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p>Analysis Type: <span className="font-medium">{reportInfo.analysisType.charAt(0).toUpperCase() + reportInfo.analysisType.slice(1)}</span></p>
            <p>Target: <span className="font-mono">{reportInfo.target}</span></p>
            <p>Generated: {
              (() => {
                try {
                  return new Date(reportInfo.timestamp.replace(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6')).toLocaleString();
                } catch (e) {
                  return 'Unknown date';
                }
              })()
            }</p>
          </div>
        )}
      </div>

      <Suspense fallback={<LoadingReport />}>
        <ReportContentWrapper filename={decodedFilename} />
      </Suspense>
    </div>
  );
}

// This wrapper component handles the async data fetching
async function ReportContentWrapper({ filename }: { filename: string }) {
  try {
    const reportData = await fetchReportData(filename);

    return (
      <ReportContent 
        content={reportData.content}
        analysisData={reportData.analysisData}
        filename={filename}
      />
    );
  } catch (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <AlertCircle className="h-6 w-6 text-red-500" />
          <h3 className="text-lg font-medium text-red-800 dark:text-red-300">
            Error Loading Report
          </h3>
        </div>
        <p className="mt-2 text-red-700 dark:text-red-300">
          {error instanceof Error ? error.message : 'An unknown error occurred while loading the report'}
        </p>
        <div className="mt-4">
          <Link 
            href="/reports"
            className="text-sm text-red-600 dark:text-red-400 hover:underline"
          >
            Return to Reports List
          </Link>
        </div>
      </div>
    );
  }
}

// Using dynamic rendering since report content should be fresh
export const dynamic = 'force-dynamic';
