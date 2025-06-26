/**
 * Infrastructure Layer Index
 * 
 * Clean Architecture의 Infrastructure Layer
 * 외부 시스템(파일시스템, 데이터베이스 등)과의 통신을 담당
 */

// FileSystem Infrastructure
export * from './filesystem/index';

// 향후 추가될 Infrastructure 구현체들
// export * from './database/index';     // 데이터베이스 구현체
// export * from './api/index';          // 외부 API 구현체
// export * from './cache/index';        // 캐시 구현체
