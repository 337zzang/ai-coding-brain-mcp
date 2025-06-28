"use strict";
/**
 * Project Entity
 *
 * Memory Bank에서 프로젝트를 나타내는 도메인 엔티티
 * 현재는 단순한 문자열 타입이지만, 향후 확장 가능
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProjectUtils = void 0;
/**
 * Project 생성/검증 헬퍼 함수들
 */
class ProjectUtils {
    /**
     * 유효한 프로젝트 이름인지 검증
     * @param name 프로젝트 이름
     * @returns 유효성 여부
     */
    static isValidProjectName(name) {
        // 기본적인 파일 시스템 안전성 검증
        const invalidChars = /[<>:"/\\|?*\x00-\x1f]/;
        return name.length > 0 && !invalidChars.test(name) && name.trim() === name;
    }
    /**
     * 프로젝트 이름 정규화
     * @param name 원본 프로젝트 이름
     * @returns 정규화된 프로젝트 이름
     */
    static normalizeProjectName(name) {
        return name.trim();
    }
}
exports.ProjectUtils = ProjectUtils;
//# sourceMappingURL=project.js.map