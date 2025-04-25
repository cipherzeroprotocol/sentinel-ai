"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Copy, Plus, Trash2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

// Define interface for API tokens
interface ApiToken {
  id: string;
  name: string;
  token?: string;
  createdAt: string;
  expiresAt?: string;
}

export default function ApiSettingsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [apiTokens, setApiTokens] = useState<ApiToken[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newTokenName, setNewTokenName] = useState("");
  const [expiresIn, setExpiresIn] = useState("30");
  const [createError, setCreateError] = useState("");
  const [newToken, setNewToken] = useState<ApiToken | null>(null);
  const [deleteTokenId, setDeleteTokenId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login?callbackUrl=/settings/api");
    }
  }, [status, router]);
  
  // Load API tokens
  useEffect(() => {
    async function loadApiTokens() {
      if (status !== "authenticated") return;
      
      setIsLoading(true);
      setError("");
      
      try {
        const response = await fetch("/api/token");
        if (!response.ok) {
          throw new Error("Failed to load API tokens");
        }
        
        const data = await response.json();
        setApiTokens(data.tokens || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "An error occurred while loading tokens";
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    }
    
    loadApiTokens();
  }, [status]);
  
  // Create new token
  const handleCreateToken = async () => {
    setCreateError("");
    
    if (!newTokenName.trim()) {
      setCreateError("Token name is required");
      return;
    }
    
    try {
      const response = await fetch("/api/token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newTokenName,
          expiresInDays: parseInt(expiresIn),
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to create token");
      }
      
      const data = await response.json();
      setNewToken(data.token as ApiToken);
      
      // Update token list
      setApiTokens([...apiTokens, data.token as ApiToken]);
      setNewTokenName("");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setCreateError(errorMessage);
    }
  };
  
  // Delete token
  const handleDeleteToken = async (id: string) => {
    setIsDeleting(true);
    
    try {
      const response = await fetch(`/api/token?id=${id}`, {
        method: "DELETE",
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to delete token");
      }
      
      // Remove from list
      setApiTokens(apiTokens.filter(token => token.id !== id));
      setDeleteTokenId(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete token";
      setError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };
  
  // Copy token to clipboard
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };
  
  if (status === "loading" || status === "unauthenticated") {
    return (
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold mb-6">API Settings</h1>
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-12 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">API Settings</h1>
      
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>API Access Tokens</CardTitle>
          <CardDescription>
            Create and manage API tokens for programmatic access to the Sentinel AI API.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" /> Create New Token
                </Button>
              </DialogTrigger>
              
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{newToken ? "Token Created" : "Create API Token"}</DialogTitle>
                  <DialogDescription>
                    {newToken 
                      ? "Make sure to copy your API token now. You won't be able to see it again." 
                      : "Create a new token to access the Sentinel AI API."}
                  </DialogDescription>
                </DialogHeader>
                
                {newToken ? (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="token">Your New API Token</Label>
                      <div className="flex mt-1">
                        <Input
                          id="token"
                          value={newToken.token}
                          readOnly
                          className="font-mono text-xs"
                        />
                        <Button
                          variant="outline"
                          onClick={() => newToken.token && copyToClipboard(newToken.token)}
                          className="ml-2"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        This token will only be displayed once. Please store it securely.
                      </AlertDescription>
                    </Alert>
                    
                    <DialogFooter>
                      <Button onClick={() => {
                        setShowCreateDialog(false);
                        setNewToken(null);
                      }}>Done</Button>
                    </DialogFooter>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {createError && (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{createError}</AlertDescription>
                      </Alert>
                    )}
                    
                    <div>
                      <Label htmlFor="token-name">Token Name</Label>
                      <Input
                        id="token-name"
                        value={newTokenName}
                        onChange={(e) => setNewTokenName(e.target.value)}
                        placeholder="My API Token"
                        className="mt-1"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="token-expiry">Expires In</Label>
                      <Select value={expiresIn} onValueChange={setExpiresIn}>
                        <SelectTrigger id="token-expiry" className="mt-1">
                          <SelectValue placeholder="Select expiration" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="7">7 days</SelectItem>
                          <SelectItem value="30">30 days</SelectItem>
                          <SelectItem value="90">90 days</SelectItem>
                          <SelectItem value="365">1 year</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                        Cancel
                      </Button>
                      <Button onClick={handleCreateToken}>Create Token</Button>
                    </DialogFooter>
                  </div>
                )}
              </DialogContent>
            </Dialog>
          </div>
          
          <div>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(2)].map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : apiTokens.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No API tokens found. Create one to get started.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {apiTokens.map((token) => (
                  <div key={token.id} className="flex items-center justify-between p-4 border rounded-md">
                    <div>
                      <div className="font-medium">{token.name}</div>
                      <div className="text-sm text-muted-foreground">
                        Created: {new Date(token.createdAt).toLocaleDateString()}
                        {token.expiresAt && ` • Expires: ${new Date(token.expiresAt).toLocaleDateString()}`}
                      </div>
                    </div>
                    
                    <Dialog open={deleteTokenId === token.id} onOpenChange={(open: boolean) => !open && setDeleteTokenId(null)}>
                      <DialogTrigger asChild>
                        <Button variant="ghost" size="sm" onClick={() => setDeleteTokenId(token.id)}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Delete API Token</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to delete this API token? This action cannot be undone.
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                          <Button variant="outline" onClick={() => setDeleteTokenId(null)}>Cancel</Button>
                          <Button 
                            variant="destructive" 
                            onClick={() => handleDeleteToken(token.id)}
                            disabled={isDeleting}
                          >
                            Delete
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Backend Connection Settings</CardTitle>
          <CardDescription>
            Configure connection settings for the Sentinel AI backend server.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="api-url">Backend API URL</Label>
              <div className="flex mt-1">
                <Input
                  id="api-url"
                  defaultValue={process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}
                  readOnly
                  className="font-mono"
                />
                <Button
                  variant="outline"
                  onClick={() => copyToClipboard(process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000")}
                  className="ml-2"
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                This URL is configured in your environment variables and cannot be changed here.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
