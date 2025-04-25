import { NextRequest, NextResponse } from "next/server";
import { getUserByEmail, initializeUsers } from "@/lib/db/users";

export async function GET(request: NextRequest) {
  try {
    // Only enable in development mode
    if (process.env.NODE_ENV !== "development") {
      return NextResponse.json({ error: "Debug endpoints disabled in production" }, { status: 403 });
    }
    
    // Force initialization of test users
    await initializeUsers();
    
    // Check if test users exist
    const adminUser = await getUserByEmail("admin@sentinel.ai");
    const analystUser = await getUserByEmail("analyst@sentinel.ai");
    const regularUser = await getUserByEmail("user@sentinel.ai");
    
    return NextResponse.json({
      users: {
        admin: adminUser ? { 
          exists: true, 
          id: adminUser.id,
          email: adminUser.email,
          role: adminUser.role,
          hasPassword: !!adminUser.password
        } : { exists: false },
        analyst: analystUser ? { 
          exists: true, 
          id: analystUser.id,
          email: analystUser.email,
          role: analystUser.role,
          hasPassword: !!analystUser.password
        } : { exists: false },
        regular: regularUser ? { 
          exists: true, 
          id: regularUser.id,
          email: regularUser.email, 
          role: regularUser.role,
          hasPassword: !!regularUser.password
        } : { exists: false }
      }
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "An error occurred", stack: error.stack }, 
      { status: 500 }
    );
  }
}
