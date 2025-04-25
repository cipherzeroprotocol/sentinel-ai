import { Radar, Shield, AlertTriangle, Search, Eye, FileText } from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12 px-4">
        <h1 className="text-4xl md:text-6xl font-bold mb-6 text-gray-900 dark:text-white">
          Sentinel <span className="text-blue-600 dark:text-blue-400">AI</span>
        </h1>
        <p className="text-xl mb-8 max-w-3xl mx-auto text-gray-700 dark:text-gray-300">
          AI-powered security analysis for the Solana blockchain. Detect malicious activities, 
          fraudulent tokens, and security threats before they affect you.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md shadow-sm"
          >
            Open Dashboard
          </Link>
          <Link
            href="/analyze"
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 font-medium rounded-md shadow-sm"
          >
            Start Analysis
          </Link>
          <Link
            href="/search"
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 font-medium rounded-md shadow-sm"
          >
            Search Entities
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 px-4">
        <h2 className="text-3xl font-bold mb-12 text-center text-gray-900 dark:text-white">
          Security Analysis Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <FeatureCard 
            icon={<Shield className="w-8 h-8 text-blue-600" />}
            title="ICO & Token Analysis"
            description="Evaluate token launches for suspicious patterns, team credibility, and technical vulnerabilities."
          />
          <FeatureCard 
            icon={<AlertTriangle className="w-8 h-8 text-red-600" />}
            title="Rugpull Detection"
            description="Identify potential rugpulls before they happen by analyzing token contracts and creator behavior."
          />
          <FeatureCard 
            icon={<Radar className="w-8 h-8 text-purple-600" />}
            title="Money Laundering Detection"
            description="Detect sophisticated money laundering techniques including layering, bridge hopping, and token swapping."
          />
          <FeatureCard 
            icon={<Eye className="w-8 h-8 text-green-600" />}
            title="Mixer Detection"
            description="Identify cryptocurrency mixing services and analyze patterns of mixer usage."
          />
          <FeatureCard 
            icon={<Search className="w-8 h-8 text-yellow-600" />}
            title="Address Poisoning Analysis"
            description="Detect address poisoning attacks and dusting campaigns targeting specific addresses."
          />
          <FeatureCard 
            icon={<FileText className="w-8 h-8 text-indigo-600" />}
            title="Comprehensive Reports"
            description="Get detailed reports with AI-powered insights, evidence collection, and security recommendations."
          />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="p-6 border border-gray-200 dark:border-gray-800 rounded-lg bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-shadow">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">{title}</h3>
      <p className="text-gray-700 dark:text-gray-300">{description}</p>
    </div>
  );
}
