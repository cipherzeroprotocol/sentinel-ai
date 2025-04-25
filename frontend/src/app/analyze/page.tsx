"use client";

import { useState, FormEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { sentinelApi, AnalysisApiResponse } from "@/lib/apiClient";
import { AlertCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = useState("address");
  const [address, setAddress] = useState("");
  const [token, setToken] = useState("");
  const [analysisType, setAnalysisType] = useState("all");
  const [days, setDays] = useState(30);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisApiResponse | null>(null);
  
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setIsLoading(true);
    
    try {
      // Log the params being sent to help debug
      console.log("Sending analysis request with params:", {
        address: activeTab === "address" ? address : undefined,
        token: activeTab === "token" ? token : undefined,
        type: analysisType,
        days
      });
      
      const response = await sentinelApi.analyze({
        address: activeTab === "address" ? address : undefined,
        token: activeTab === "token" ? token : undefined,
        type: analysisType,
        days
      });
      
      console.log("Analysis response:", response);
      setResult(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred during analysis";
      console.error("Analysis error:", errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Analyze</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Start New Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-6">
              <TabsTrigger value="address">Analyze Address</TabsTrigger>
              <TabsTrigger value="token">Analyze Token</TabsTrigger>
            </TabsList>
            
            <form onSubmit={handleSubmit}>
              <TabsContent value="address" className="space-y-4">
                <div>
                  <Label htmlFor="address">Solana Address</Label>
                  <Input 
                    id="address" 
                    value={address} 
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Enter Solana address to analyze"
                    required
                  />
                </div>
              </TabsContent>
              
              <TabsContent value="token" className="space-y-4">
                <div>
                  <Label htmlFor="token">Token Address</Label>
                  <Input 
                    id="token" 
                    value={token} 
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Enter token address to analyze"
                    required
                  />
                </div>
              </TabsContent>
              
              <div className="mt-6 space-y-4">
                <div>
                  <Label>Analysis Type</Label>
                  <RadioGroup 
                    value={analysisType} 
                    onValueChange={(newValue) => {
                      console.log("Selected analysis type:", newValue);
                      setAnalysisType(newValue);
                    }}
                    className="flex flex-wrap gap-4 mt-2"
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="all" id="all" />
                      <Label htmlFor="all">All Analyses</Label>
                    </div>
                    
                    {activeTab === "address" && (
                      <>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="wallet" id="wallet" />
                          <Label htmlFor="wallet">Wallet Profile</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="transaction" id="transaction" />
                          <Label htmlFor="transaction">Transaction History</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="money_laundering" id="money_laundering" />
                          <Label htmlFor="money_laundering">Money Laundering</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="mixer" id="mixer" />
                          <Label htmlFor="mixer">Mixer Detection</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="dusting" id="dusting" />
                          <Label htmlFor="dusting">Dusting Analysis</Label>
                        </div>
                      </>
                    )}
                    
                    {activeTab === "token" && (
                      <>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="ico" id="ico" />
                          <Label htmlFor="ico">ICO Analysis</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="rugpull" id="rugpull" />
                          <Label htmlFor="rugpull">Rugpull Detection</Label>
                        </div>
                      </>
                    )}
                  </RadioGroup>
                </div>
                
                <div>
                  <Label htmlFor="days">Time Range (days)</Label>
                  <Input 
                    id="days" 
                    type="number" 
                    min={1}
                    max={365}
                    value={days} 
                    onChange={(e) => setDays(parseInt(e.target.value))}
                    className="max-w-[200px]"
                  />
                </div>
                
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                
                <Button type="submit" disabled={isLoading} className="mt-4">
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Start Analysis"
                  )}
                </Button>
              </div>
            </form>
          </Tabs>
        </CardContent>
      </Card>
      
      {result && (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-slate-100 dark:bg-slate-900 p-4 rounded-md overflow-auto max-h-[500px]">
              {JSON.stringify(result, null, 2)}
            </pre>
            
            {result.report_path && (
              <div className="mt-4">
                <Button asChild>
                  <a href={`/reports/${result.report_path}`} target="_blank" rel="noopener noreferrer">
                    View Full Report
                  </a>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
