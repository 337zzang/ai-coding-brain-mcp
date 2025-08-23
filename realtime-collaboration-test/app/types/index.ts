// 전역 타입 정의
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Room {
  id: string;
  name: string;
  description?: string;
  createdBy: string;
  members: string[];
  isPrivate: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed';

// 재사용 가능한 컴포넌트 props
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}