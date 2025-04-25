import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

// Export a middleware function that includes Next.js Edge Runtime
export default withAuth(
  function middleware(req) {
    // For debugging: log the token presence
    console.log(`Middleware - token exists: ${!!req.nextauth.token}`);
    
    // Just continue the request if authentication checks passed
    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => {
        // This is the key check - MUST return true if token exists
        return !!token;
      },
    },
    pages: {
      signIn: "/login",
    }
  }
);

// Configure which routes require authentication
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - / (home page)
     * - /login (login page)
     * - /api routes that don't require auth
     * - /_next/static (static files)
     * - /_next/image (image optimization)
     * - /favicon.ico (favicon)
     */
    '/((?!api/auth|login|_next/static|_next/image|favicon.ico).*)',
  ],
};
