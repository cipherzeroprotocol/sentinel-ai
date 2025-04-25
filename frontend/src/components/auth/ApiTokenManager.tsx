import { useState, useEffect } from 'react';
import { Plus, Trash2, Copy, Check, AlertCircle } from 'lucide-react';
import { ApiToken } from '@/types';

interface ApiTokenManagerProps {
  className?: string;
}

const ApiTokenManager: React.FC<ApiTokenManagerProps> = ({ className = '' }) => {
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newTokenName, setNewTokenName] = useState('');
  const [expiryDays, setExpiryDays] = useState(30);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [newlyCreatedToken, setNewlyCreatedToken] = useState<ApiToken | null>(null);

  // Load tokens
  useEffect(() => {
    async function fetchTokens() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch('/api/token');
        
        if (!response.ok) {
          throw new Error('Failed to load API tokens');
        }
        
        const data = await response.json();
        setTokens(data.tokens || []);
      } catch (err: any) {
        setError(err.message || 'An error occurred while loading API tokens');
      } finally {
        setLoading(false);
      }
    }
    
    fetchTokens();
  }, []);

  // Create token
  const handleCreateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newTokenName.trim()) {
      return;
    }
    
    try {
      setIsCreating(true);
      setError(null);
      
      const response = await fetch('/api/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: newTokenName, 
          expiresInDays: expiryDays > 0 ? expiryDays : undefined 
        })
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to create token');
      }
      
      const { token } = await response.json();
      
      // Add new token to list
      setTokens(prev => [...prev, token]);
      
      // Save newly created token to show full value
      setNewlyCreatedToken(token);
      
      // Reset form
      setNewTokenName('');
      setIsCreating(false);
    } catch (err: any) {
      setError(err.message || 'Failed to create API token');
      setIsCreating(false);
    }
  };

  // Delete token
  const handleDeleteToken = async (tokenId: string) => {
    try {
      setError(null);
      
      const response = await fetch(`/api/token?id=${tokenId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to delete token');
      }
      
      // Remove token from list
      setTokens(prev => prev.filter(t => t.id !== tokenId));
      
      // Clear newly created token if it was deleted
      if (newlyCreatedToken?.id === tokenId) {
        setNewlyCreatedToken(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete API token');
    }
  };

  // Copy token to clipboard
  const copyToClipboard = (token: string) => {
    navigator.clipboard.writeText(token)
      .then(() => {
        setCopiedToken(token);
        setTimeout(() => setCopiedToken(null), 2000);
      })
      .catch(err => {
        console.error('Failed to copy token:', err);
      });
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">API Tokens</h2>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="mr-2 h-4 w-4" />
          New Token
        </button>
      </div>
      
      {/* Error display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-md flex items-start">
          <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}
      
      {/* Token creation form */}
      {isCreating && (
        <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 p-4 rounded-md">
          <h3 className="text-lg font-medium mb-3 text-gray-900 dark:text-white">Create New API Token</h3>
          <form onSubmit={handleCreateToken} className="space-y-4">
            <div>
              <label htmlFor="tokenName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Token Name
              </label>
              <input
                type="text"
                id="tokenName"
                placeholder="My API Token"
                value={newTokenName}
                onChange={(e) => setNewTokenName(e.target.value)}
                className="px-3 py-2 w-full border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            
            <div>
              <label htmlFor="expiryDays" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Expiration (days)
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  id="expiryDays"
                  min="1"
                  max="365"
                  placeholder="30"
                  value={expiryDays}
                  onChange={(e) => setExpiryDays(Number(e.target.value))}
                  className="px-3 py-2 w-32 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  (set to 0 for no expiration)
                </span>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!newTokenName.trim() || isCreating}
                className="px-3 py-2 text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
              >
                Create Token
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Newly created token display */}
      {newlyCreatedToken && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 rounded-md">
          <h4 className="text-sm font-medium text-green-800 dark:text-green-300 mb-2">
            Token created successfully
          </h4>
          <p className="text-xs text-green-700 dark:text-green-400 mb-1">
            Copy this token now. You won't be able to see it again!
          </p>
          <div className="flex items-center bg-white dark:bg-gray-800 p-2 rounded border border-gray-300 dark:border-gray-600">
            <code className="font-mono text-sm flex-1 overflow-x-auto whitespace-nowrap px-1 py-0.5">
              {newlyCreatedToken.token}
            </code>
            <button
              onClick={() => copyToClipboard(newlyCreatedToken.token)}
              className="ml-2 p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Copy to clipboard"
            >
              {copiedToken === newlyCreatedToken.token ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>
        </div>
      )}
      
      {/* Tokens list */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
        <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Your API Tokens</h3>
        </div>
        
        {loading ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            Loading tokens...
          </div>
        ) : tokens.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            No API tokens found. Create your first token above.
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {tokens.map(token => (
              <li key={token.id} className="px-4 py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                      {token.name}
                    </h4>
                    <div className="flex space-x-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                      <span>Created: {formatDate(token.createdAt)}</span>
                      {token.expiresAt && <span>Expires: {formatDate(token.expiresAt)}</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteToken(token.id)}
                    className="p-1 text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400"
                    title="Delete token"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-1 text-xs flex items-center font-mono">
                  <span className="text-gray-500 dark:text-gray-400">
                    {token.token.substring(0, 10)}...
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-md text-sm text-blue-700 dark:text-blue-300">
        <h4 className="font-medium mb-1">Using API Tokens</h4>
        <p className="mb-2">Include your API token in request headers:</p>
        <code className="block bg-white dark:bg-gray-800 p-2 rounded font-mono text-xs whitespace-nowrap overflow-x-auto border border-blue-200 dark:border-blue-800">
          Authorization: Bearer YOUR_API_TOKEN
        </code>
      </div>
    </div>
  );
};

export default ApiTokenManager;
