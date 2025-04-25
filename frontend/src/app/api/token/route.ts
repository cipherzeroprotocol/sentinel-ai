import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { createApiToken, deleteApiToken, getUserById } from "@/lib/db/users";
import { authOptions } from "@/lib/auth";

// Create new API token
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    // Check authentication
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Authentication required" }, { status: 401 });
    }
    
    const { name, expiresInDays } = await request.json();
    
    if (!name) {
      return NextResponse.json({ error: "Token name is required" }, { status: 400 });
    }
    
    const token = await createApiToken(session.user.id, name, expiresInDays);
    
    if (!token) {
      return NextResponse.json({ error: "Failed to create token" }, { status: 500 });
    }
    
    return NextResponse.json({ success: true, token });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "An error occurred" }, 
      { status: 500 }
    );
  }
}

// Delete API token
export async function DELETE(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    // Check authentication
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Authentication required" }, { status: 401 });
    }
    
    const { searchParams } = new URL(request.url);
    const tokenId = searchParams.get('id');
    
    if (!tokenId) {
      return NextResponse.json({ error: "Token ID is required" }, { status: 400 });
    }
    
    const success = await deleteApiToken(session.user.id, tokenId);
    
    if (!success) {
      return NextResponse.json({ error: "Failed to delete token" }, { status: 404 });
    }
    
    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "An error occurred" }, 
      { status: 500 }
    );
  }
}

// Get all tokens for current user
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
    
    return NextResponse.json({ tokens: user.apiTokens || [] });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "An error occurred" }, 
      { status: 500 }
    );
  }
}
