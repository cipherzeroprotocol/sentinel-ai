// Define UserRole enum for use across the application
export enum UserRole {
  ADMIN = "admin",
  ANALYST = "analyst",
  USER = "user"
}

// Remove the next-auth module declarations since they're already defined in src/types/next-auth.d.ts
// The duplicate declarations were causing the TypeScript errors

// Add other application-specific types here as needed
export interface ApiTokenCreate {
  name: string;
  expiresInDays?: number;
}

export interface ApiToken {
  id: string;
  name: string;
  token?: string;
  createdAt: string;
  expiresAt?: string;
}

// You can define other application types here
