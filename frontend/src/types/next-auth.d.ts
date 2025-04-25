import NextAuth, { DefaultSession, DefaultUser } from "next-auth";
import { JWT, DefaultJWT } from "next-auth/jwt";
import { UserRole } from "@/types"; // Assuming UserRole is defined here or import appropriately

declare module "next-auth" {
  /**
   * Returned by `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    user: {
      id: string;
      email?: string | null;
      name?: string | null;
      image?: string | null;
      role: UserRole; // Or string if UserRole is not an enum/type
      preferences?: any; // Add the preferences property, define its type more accurately if possible
    } & DefaultSession["user"]; // Keep the default properties like name, email, image
    accessToken: string; // Add the custom accessToken property
  }

  /**
   * The shape of the user object returned in the OAuth providers' `profile` callback,
   * or the second parameter of the `session` callback, when using a database.
   */
  interface User extends DefaultUser {
    id: string;
    email: string;
    name?: string;
    role: UserRole; // Or string
    preferences?: any; // Add preferences if it comes from the authorize callback user object
  }
}

declare module "next-auth/jwt" {
  /** Returned by the `jwt` callback and `getToken`, when using JWT sessions */
  interface JWT extends DefaultJWT {
    id: string;
    email: string;
    name?: string;
    role: UserRole; // Or string
    accessToken: string; // Add the custom accessToken property
  }
}
