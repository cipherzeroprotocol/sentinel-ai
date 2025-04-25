import NextAuth from "next-auth";
// Remove local imports related to authOptions definition
// import { type NextAuthOptions, User, Session } from "next-auth";
// import CredentialsProvider from "next-auth/providers/credentials";
// import { compare } from "bcryptjs";
// import { getUserByEmail, getUserById } from "@/lib/db/users";
// import { UserRole } from "@/types";
// import { JWT } from "next-auth/jwt";

// Import authOptions from the new location
import { authOptions } from "@/lib/auth";

// Remove the authOptions definition from this file
// export const authOptions: NextAuthOptions = { ... };

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
