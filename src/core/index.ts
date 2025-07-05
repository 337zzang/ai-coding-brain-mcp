/**
 * Core Module Index
 * 
 * Clean Architecture의 핵심 레이어들을 export
 * Domain과 Infrastructure 레이어 포함
 */

// Domain Layer (엔티티, Repository 인터페이스)
export * from './domain/index';

// Infrastructure Layer (Repository 구현체들)
export * from './infrastructure/index';

// 향후 추가될 레이어들
// export * from './application/index';  // Application/Use Case Layer
// export * from './presentation/index'; // Presentation Layer (MCP 컨트롤러들)
