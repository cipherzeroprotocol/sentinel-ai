import { type NextAuthOptions, User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { compare } from "bcryptjs";
import { getUserByEmail, getUserById } from "@/lib/db/users";
import { UserRole, UserPreferences } from "@/types";

// Define explicit types instead of augmenting NextAuth types
export interface SentinelUser {
  id: string;
  name?: string | null;
  email?: string | null;
  image?: string | null;
  role?: UserRole;
  preferences?: UserPreferences;
}

export interface SentinelSession {
  user: SentinelUser;
  expires: string;
  accessToken?: string;
}

export interface SentinelToken {
  id: string;
  name?: string | null;
  email?: string | null;
  picture?: string | null;
  role?: UserRole;
  accessToken?: string;
  preferences?: UserPreferences;
  iat?: number;
  exp?: number;
  jti?: string;
}

export const authOptions: NextAuthOptions = {
  // Debug mode for development - remember to turn off in production
  debug: process.env.NODE_ENV === 'development',
  
  pages: {
    signIn: "/login",
    // You can add other custom pages if needed
    // signOut: '/signout',
    // error: '/auth/error',
  },
  
  session: {
    strategy: "jwt",
    // Increase maxAge if sessions are expiring too quickly
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password are required");
        }

        const user = await getUserByEmail(credentials.email);
        
        if (!user) {
          console.log(`User not found: ${credentials.email}`);
          throw new Error("Invalid email or password");
        }

        if (!user.password) {
          console.log(`User has no password: ${user.email}`);
          throw new Error("Invalid email or password");
        }

        const isPasswordValid = await compare(credentials.password, user.password);
        
        if (!isPasswordValid) {
          console.log(`Invalid password for user: ${user.email}`);
          throw new Error("Invalid email or password");
        }
        
        // Return user data that will be stored in the token
        return {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role
        };
      }
    })
  ],
  
  callbacks: {
    async jwt({ token, user }) {
      // When signing in, add user info to the token
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
        token.role = user.role;
      }
      return token;
    },
    
    async session({ session, token }) {
      // Add user info from token to the session
      if (token) {
        session.user = {
          id: token.id as string,
          email: token.email as string,
          name: token.name as string,
          role: token.role as UserRole
        };
      }
      return session;
    }
  }
};

// Helper to check if user has required role - use our explicit type
export function hasRequiredRole(user: SentinelUser | null, requiredRole: UserRole | UserRole[]): boolean {
  if (!user?.role) return false;

  const { role } = user;

  if (Array.isArray(requiredRole)) {
    return requiredRole.includes(role as UserRole);
  }
  return role === requiredRole;
}

// API token helpers
export function generateApiToken(): string {
  // Generate a random token - in production use a more secure method
  return `sentinel_${Math.random().toString(36).substring(2)}${Date.now().toString(36)}`;
}

// Protected route middleware helper
export function isAuthenticated(session: any): boolean {
  return !!session?.user?.id;
}
