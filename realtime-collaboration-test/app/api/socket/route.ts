// Socket.io API 라우트 - App Router 방식
import { NextRequest, NextResponse } from 'next/server'
import { Server } from 'socket.io'
import type { 
  ServerToClientEvents, 
  ClientToServerEvents 
} from '@/app/types/socket'

// App Router에서는 Socket.io 직접 사용이 제한적
// 대안으로 Server-Sent Events나 WebSocket API 사용 권장
export async function GET(request: NextRequest) {
  return NextResponse.json({
    message: 'Socket.io endpoint - use Pages API instead',
    redirectTo: '/api/socket'
  })
}

export async function POST(request: NextRequest) {
  const body = await request.json()

  // 메시지 처리 로직 (예시)
  return NextResponse.json({
    success: true,
    message: 'Message processed',
    data: body
  })
}