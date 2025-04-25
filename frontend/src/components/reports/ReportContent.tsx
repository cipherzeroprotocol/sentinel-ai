'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { FileJson, FileText, Download } from 'lucide-react';

// Function to save file (replacement for saveAs from file-saver)
const saveAs = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

// Define prop types
interface ReportContentProps {
  content: string;
  analysisData: any;
  filename: string;
}

export default function ReportContent({ 
  content, 
  analysisData, 
  filename 
}: ReportContentProps) {
  const [activeTab, setActiveTab] = useState(analysisData ? 'interactive' : 'markdown');
  const [isLoadingPDF, setIsLoadingPDF] = useState(false);

  // Export as JSON function
  const exportAsJSON = () => {
    if (!analysisData) return;
    
    try {
      const jsonString = JSON.stringify(analysisData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      saveAs(blob, `${filename.replace('.md', '')}.json`);
    } catch (err) {
      console.error("Error exporting JSON:", err);
      alert("Failed to export data as JSON");
    }
  };

  // Export as PDF function (simplified, would use a proper PDF generation library)
  const exportAsPDF = async () => {
    setIsLoadingPDF(true);
    try {
      alert("PDF export functionality would be implemented here");
    } catch (error) {
      console.error("Error generating PDF:", error);
    } finally {
      setIsLoadingPDF(false);
    }
  };

  // Base URL for report images served by the backend
  const reportBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
  
  return (
    <div className="space-y-6">
      {/* Export buttons */}
      {analysisData && (
        <div className="flex justify-end gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={exportAsJSON}
            className="flex items-center gap-1"
          >
            <FileJson className="h-4 w-4" />
            Export as JSON
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={exportAsPDF}
            disabled={isLoadingPDF}
            className="flex items-center gap-1"
          >
            <Download className="h-4 w-4" />
            {isLoadingPDF ? 'Generating PDF...' : 'Export as PDF'}
          </Button>
        </div>
      )}

      {/* Report content */}
      <div id="report-content">
        {analysisData ? (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="interactive" className="flex items-center gap-2">
                <FileJson className="h-4 w-4" />
                Interactive Report
              </TabsTrigger>
              <TabsTrigger value="markdown" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Markdown
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="interactive" className="space-y-6">
              {/* This section would have interactive visualizations based on report data */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-semibold mb-4">Analysis Summary</h2>
                
                {analysisData.risk_score !== undefined && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium mb-2">Risk Assessment</h3>
                    <div className="flex items-center gap-4">
                      <div className="text-3xl font-bold">
                        {analysisData.risk_score}/100
                      </div>
                      <div className="text-lg">
                        {getRiskLabel(analysisData.risk_score)}
                      </div>
                    </div>
                  </div>
                )}
                
                {analysisData.risk_factors && analysisData.risk_factors.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium mb-2">Risk Factors</h3>
                    <ul className="list-disc pl-5 space-y-1">
                      {analysisData.risk_factors.map((factor: string, index: number) => (
                        <li key={index}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <pre className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-md overflow-auto text-xs">
                  {JSON.stringify(analysisData, null, 2)}
                </pre>
              </div>
            </TabsContent>
            
            <TabsContent value="markdown">
              <div className="prose dark:prose-invert prose-sm sm:prose-base lg:prose-lg max-w-none bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    img: ({src, alt, ...props}) => {
                      // Handle relative image paths
                      const imageSrc = src && src.startsWith('./') 
                        ? `${reportBaseUrl}/generated_reports/${filename.split('/').slice(0, -1).join('/')}/${src.substring(2)}` 
                        : src;
                      return <img src={imageSrc} alt={alt} className="max-w-full rounded-md" {...props} />;
                    }
                  }}
                >
                  {content}
                </ReactMarkdown>
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          // Simple markdown rendering if no analysis data is available
          <div className="prose dark:prose-invert prose-sm sm:prose-base lg:prose-lg max-w-none bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                img: ({src, alt, ...props}) => {
                  // Handle relative image paths
                  const imageSrc = src && src.startsWith('./') 
                    ? `${reportBaseUrl}/generated_reports/${src.substring(2)}` 
                    : src;
                  return <img src={imageSrc} alt={alt} className="max-w-full rounded-md" {...props} />;
                }
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper function to determine risk label from score
function getRiskLabel(score: number): string {
  if (score >= 80) return "Very High Risk";
  if (score >= 60) return "High Risk";
  if (score >= 40) return "Medium Risk";
  if (score >= 20) return "Low Risk";
  return "Very Low Risk";
}
