"use strict";
/**
 * Infrastructure Layer Index
 *
 * Clean Architecture의 Infrastructure Layer
 * 외부 시스템(파일시스템, 데이터베이스 등)과의 통신을 담당
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
// FileSystem Infrastructure
__exportStar(require("./filesystem/index"), exports);
// 향후 추가될 Infrastructure 구현체들
// export * from './database/index';     // 데이터베이스 구현체
// export * from './api/index';          // 외부 API 구현체
// export * from './cache/index';        // 캐시 구현체
//# sourceMappingURL=index.js.map