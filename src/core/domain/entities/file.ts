/**
 * File Entity
 * 
 * Memory Bank에서 파일을 나타내는 도메인 엔티티
 * 현재는 단순한 문자열 타입이지만, 향후 확장 가능
 */

export type File = string;

/**
 * File 관련 유틸리티 타입들
 */
export interface FileInfo {
  name: File;
  content: string;
  size: number;
  lastModified: Date;
  exists: boolean;
}

export interface FileMetadata {
  name: File;
  size: number;
  lastModified: Date;
  encoding: string;
}

/**
 * File 생성/검증 헬퍼 함수들
 */
export class FileUtils {
  /**
   * 유효한 파일 이름인지 검증
   * @param name 파일 이름
   * @returns 유효성 여부
   */
  static isValidFileName(name: string): boolean {
    // 기본적인 파일 시스템 안전성 검증
    const invalidChars = /[<>:"/\\|?*\x00-\x1f]/;
    const reservedNames = /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i;
    
    return (
      name.length > 0 &&
      name.length <= 255 &&
      !invalidChars.test(name) &&
      !reservedNames.test(name) &&
      name.trim() === name &&
      !name.endsWith('.')
    );
  }

  /**
   * 파일 이름 정규화
   * @param name 원본 파일 이름
   * @returns 정규화된 파일 이름
   */
  static normalizeFileName(name: string): File {
    return name.trim();
  }

  /**
   * 파일 확장자 추출
   * @param name 파일 이름
   * @returns 파일 확장자 (점 포함)
   */
  static getFileExtension(name: string): string {
    const lastDotIndex = name.lastIndexOf('.');
    return lastDotIndex !== -1 ? name.substring(lastDotIndex) : '';
  }

  /**
   * 파일 이름에서 확장자 제거
   * @param name 파일 이름
   * @returns 확장자가 제거된 파일 이름
   */
  static getFileNameWithoutExtension(name: string): string {
    const lastDotIndex = name.lastIndexOf('.');
    return lastDotIndex !== -1 ? name.substring(0, lastDotIndex) : name;
  }
}
