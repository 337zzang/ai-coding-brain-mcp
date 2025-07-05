/**
 * File Repository Interface
 * 
 * 파일 관련 데이터 접근을 추상화하는 인터페이스
 * Clean Architecture의 Data Layer에서 사용
 */

import { File } from '../entities/index';

export interface FileRepository {
  /**
   * 프로젝트 내 모든 파일 목록 조회
   * @param projectName 프로젝트 이름
   * @returns 파일 이름 배열
   */
  listFiles(projectName: string): Promise<File[]>;

  /**
   * 파일 내용 로드
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 파일 내용 (파일이 없으면 null)
   */
  loadFile(projectName: string, fileName: string): Promise<string | null>;

  /**
   * 파일 작성 (생성 또는 덮어쓰기)
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @param content 파일 내용
   * @param force 기존 파일 덮어쓰기 여부 (기본값: false)
   * @returns 작성된 파일 내용 (실패시 null)
   */
  writeFile(
    projectName: string,
    fileName: string,
    content: string,
    force?: boolean
  ): Promise<File | null>;

  /**
   * 파일 존재 여부 확인
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 존재 여부
   */
  fileExists?(projectName: string, fileName: string): Promise<boolean>;

  /**
   * 파일 삭제
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 삭제 성공 여부
   */
  deleteFile?(projectName: string, fileName: string): Promise<boolean>;

  /**
   * 파일 이름 변경
   * @param projectName 프로젝트 이름
   * @param oldFileName 기존 파일 이름
   * @param newFileName 새 파일 이름
   * @returns 변경 성공 여부
   */
  renameFile?(
    projectName: string,
    oldFileName: string,
    newFileName: string
  ): Promise<boolean>;

  /**
   * 파일 메타데이터 조회
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 파일 메타데이터
   */
  getFileMetadata?(projectName: string, fileName: string): Promise<{
    name: string;
    size: number;
    lastModified: Date;
    encoding: string;
  } | null>;

  /**
   * 파일 부분 편집 (특정 내용 찾아서 교체)
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @param oldContent 찾을 기존 내용
   * @param newContent 교체할 새 내용
   * @param expectedOccurrences 예상 교체 횟수 (기본값: 1)
   * @returns 편집 결과 정보
   */
  editFile?(
    projectName: string,
    fileName: string,
    oldContent: string,
    newContent: string,
    expectedOccurrences?: number
  ): Promise<{
    success: boolean;
    actualOccurrences: number;
    updatedContent: string | null;
    message: string;
  }>;
}
