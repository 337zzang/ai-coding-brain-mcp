// Socket.io API 라우트 - Next.js 13 이하 호환
import { NextApiRequest, NextApiResponse } from 'next'
import { Server } from 'socket.io'
import type { 
  ServerToClientEvents, 
  ClientToServerEvents 
} from '@/app/types/socket'

export default function SocketHandler(
  req: NextApiRequest, 
  res: NextApiResponse
) {
  if (res.socket.server.io) {
    console.log('Socket.io already initialized')
    res.end()
    return
  }

  console.log('Initializing Socket.io server...')

  const io = new Server<ClientToServerEvents, ServerToClientEvents>(
    res.socket.server, {
      path: '/api/socket',
      addTrailingSlash: false,
      cors: {
        origin: process.env.NODE_ENV === 'development' 
          ? 'http://localhost:3000' 
          : process.env.NEXT_PUBLIC_APP_URL,
        methods: ['GET', 'POST']
      }
    }
  )

  io.on('connection', (socket) => {
    console.log(`User connected: ${socket.id}`)

    // 방 입장 처리
    socket.on('join-room', (roomId: string) => {
      socket.join(roomId)
      socket.to(roomId).emit('user-joined', {
        id: socket.id,
        name: 'Anonymous User',
        email: '',
        isOnline: true,
        lastSeen: new Date()
      })
      console.log(`User ${socket.id} joined room ${roomId}`)
    })

    // 메시지 전송 처리
    socket.on('send-message', (messageData) => {
      const message = {
        ...messageData,
        id: `msg_${Date.now()}`,
        timestamp: new Date()
      }

      // 같은 방의 모든 사용자에게 메시지 전송
      socket.broadcast.emit('message-received', message)
    })

    // 협업 이벤트 처리
    socket.on('collaboration-update', (eventData) => {
      const event = {
        ...eventData,
        timestamp: new Date()
      }

      socket.broadcast.emit('collaboration-event', event)
    })

    // 연결 해제 처리
    socket.on('disconnect', () => {
      console.log(`User disconnected: ${socket.id}`)
    })
  })

  res.socket.server.io = io
  res.end()
}