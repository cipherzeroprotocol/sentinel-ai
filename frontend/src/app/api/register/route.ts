import { NextRequest, NextResponse } from "next/server";
import { createUser, getUserByEmail } from "@/lib/db/users";
import { UserRole } from "@/types";

export async function POST(request: NextRequest) {
  try {
    // In a production app, you might want to restrict registration
    // or require admin approval for new accounts
    const { email, password, name } = await request.json();
    
    // Simple validation
    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" }, 
        { status: 400 }
      );
    }
    
    // Check if user already exists
    const existingUser = await getUserByEmail(email);
    if (existingUser) {
      return NextResponse.json(
        { error: "User with this email already exists" }, 
        { status: 409 }
      );
    }
    
    // Create new user (as regular user by default)
    const user = await createUser({
      email,
      password,
      name,
      role: UserRole.USER // Default role
    });
    
    return NextResponse.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role
      }
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "An error occurred" }, 
      { status: 500 }
    );
  }
}
