import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    // Only enable in development mode
    if (process.env.NODE_ENV !== 'development') {
      return NextResponse.json({ error: 'Debug endpoints disabled in production' }, { status: 403 });
    }

    const session = await getServerSession(authOptions);

    if (!session) {
      return NextResponse.json({ 
        authorized: false, 
        message: 'No active session found' 
      });
    }

    return NextResponse.json({
      authorized: true,
      session: {
        user: {
          id: session.user.id,
          email: session.user.email,
          name: session.user.name,
          role: session.user.role
        },
        expires: session.expires
      }
    });
  } catch (error: any) {
    console.error('Session debug error:', error);
    return NextResponse.json(
      { error: error.message || 'An error occurred checking session' },
      { status: 500 }
    );
  }
}
