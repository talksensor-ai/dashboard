import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
    
    if (!supabaseUrl) {
      return NextResponse.json({ serverTime: Date.now() });
    }
    
    // Send a HEAD request to Supabase to get headers (specifically the Date header)
    const res = await fetch(`${supabaseUrl}/rest/v1/agent_telemetry?limit=1`, {
      method: 'HEAD',
      headers: {
        'apikey': supabaseKey,
      },
      cache: 'no-store'
    });
    
    const serverDate = res.headers.get('date');
    return NextResponse.json({ 
      serverTime: serverDate ? new Date(serverDate).getTime() : Date.now() 
    });
  } catch (e) {
    console.error("Error in server-time route:", e);
    return NextResponse.json({ serverTime: Date.now() });
  }
}
