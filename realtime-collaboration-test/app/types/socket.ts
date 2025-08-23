// Socket.io 관련 타입 정의
export interface SocketUser {
  id: string;
  name: string;
  email: string;
  isOnline: boolean;
  lastSeen: Date;
}

export interface ChatMessage {
  id: string;
  userId: string;
  content: string;
  timestamp: Date;
  type: 'text' | 'file' | 'system';
}

export interface CollaborationEvent {
  type: 'cursor-move' | 'text-change' | 'selection-change';
  userId: string;
  data: any;
  timestamp: Date;
}

// Server to Client Events
export interface ServerToClientEvents {
  'user-joined': (user: SocketUser) => void;
  'user-left': (userId: string) => void;
  'message-received': (message: ChatMessage) => void;
  'collaboration-event': (event: CollaborationEvent) => void;
  'user-list-updated': (users: SocketUser[]) => void;
}

// Client to Server Events  
export interface ClientToServerEvents {
  'join-room': (roomId: string) => void;
  'leave-room': (roomId: string) => void;
  'send-message': (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  'collaboration-update': (event: Omit<CollaborationEvent, 'timestamp'>) => void;
}