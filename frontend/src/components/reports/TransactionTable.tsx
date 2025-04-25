import React from 'react';

import { Badge } from "@/components/ui/badge"; // For status badges
import { formatDistanceToNow } from 'date-fns'; // For relative dates
import { 
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell
} from "@/components/ui/table"; // Import table components

// Define a more specific type for transactions based on usage in DetailedReportView
// This is a guess based on common transaction fields, adjust as needed
interface Transaction {
  signature?: string; // Often used as ID in blockchain contexts
  timestamp?: number | string; // Unix timestamp or ISO string
  description?: string; // May need to be constructed
  amount?: number | string; // Amount transferred
  status?: string; // e.g., 'Confirmed', 'Pending', 'Failed'
  from_address?: string;
  to_address?: string;
  token_symbol?: string;
  value_usd?: number;
  type?: string; // e.g., 'Transfer', 'Swap', 'Contract Interaction'
  [key: string]: any; // Allow other fields
}

interface TransactionTableProps {
  transactions: Transaction[];
}

const TransactionTable: React.FC<TransactionTableProps> = ({ transactions }) => {

  const formatTimestamp = (timestamp: number | string | undefined): string => {
    if (!timestamp) return 'N/A';
    try {
      const date = new Date(typeof timestamp === 'string' ? timestamp : timestamp * 1000);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch (e) {
      return 'Invalid Date';
    }
  };

  const formatAddress = (address: string | undefined): string => {
    if (!address) return 'N/A';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  const formatAmount = (tx: Transaction): string => {
    if (tx.amount === undefined || tx.amount === null) return 'N/A';
    const amountStr = typeof tx.amount === 'number' ? tx.amount.toFixed(6) : tx.amount;
    return `${amountStr} ${tx.token_symbol || ''}`.trim();
  };

  const formatValue = (value: number | undefined): string => {
    if (value === undefined || value === null) return 'N/A';
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="transaction-table">
      {transactions.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>From</TableHead>
              <TableHead>To</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">Value (USD)</TableHead>
              <TableHead className="text-center">Status</TableHead>
              <TableHead className="text-right">Signature</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx, index) => (
              <TableRow key={tx.signature || `tx-${index}`}>
                <TableCell className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                  {formatTimestamp(tx.timestamp)}
                </TableCell>
                <TableCell className="font-medium">{tx.type || 'Unknown'}</TableCell>
                <TableCell className="font-mono text-xs">{formatAddress(tx.from_address)}</TableCell>
                <TableCell className="font-mono text-xs">{formatAddress(tx.to_address)}</TableCell>
                <TableCell className="text-right font-medium">{formatAmount(tx)}</TableCell>
                <TableCell className="text-right text-gray-600 dark:text-gray-300">{formatValue(tx.value_usd)}</TableCell>
                <TableCell className="text-center">
                  {tx.status ? (
                    <Badge variant={tx.status.toLowerCase() === 'confirmed' ? 'secondary' : 'outline'}>
                      {tx.status}
                    </Badge>
                  ) : (
                    '-'
                  )}
                </TableCell>
                <TableCell className="text-right font-mono text-xs">
                  {tx.signature ? formatAddress(tx.signature) : 'N/A'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-gray-500 dark:text-gray-400 py-4 text-center">No transactions found for this analysis.</p>
      )}
    </div>
  );
};

export default TransactionTable;
