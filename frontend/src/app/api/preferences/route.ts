import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { getUserById, updateUserPreferences } from "@/lib/db/users";
import { authOptions } from "@/lib/auth";

// Get user preferences
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    // Check authentication
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Authentication required" }, { status: 401 });
    }
    
    const user = await getUserById(session.user.id);
    
    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }
    
    return NextResponse.json({ preferences: user.preferences || {} });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "An error occurred" }, 
      { status: 500 }
    );
  }
}

// Update user preferences
export async function PATCH(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    // Check authentication
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Authentication required" }, { status: 401 });
    }
    
    const preferences = await request.json();
    
    if (typeof preferences !== 'object' || preferences === null) {
      return NextResponse.json({ error: "Invalid preferences data" }, { status: 400 });
    }
    
    const user = await updateUserPreferences(session.user.id, preferences);
    
    if (!user) {
      return NextResponse.json({ error: "Failed to update preferences" }, { status: 500 });
    }
    
    return NextResponse.json({ success: true, preferences: user.preferences });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "An error occurred" }, 
      { status: 500 }
    );
  }
}
