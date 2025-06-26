/**
 * Project Repository Interface
 * 
 * 프로젝트 관련 데이터 접근을 추상화하는 인터페이스
 * Clean Architecture의 Data Layer에서 사용
 */

import { Project } from '../entities/index';

export interface ProjectRepository {
  /**
   * 모든 프로젝트 목록 조회
   * @returns 프로젝트 배열
   */
  listProjects(): Promise<Project[]>;

  /**
   * 프로젝트 존재 여부 확인
   * @param name 프로젝트 이름
   * @returns 존재 여부
   */
  projectExists(name: string): Promise<boolean>;

  /**
   * 프로젝트 디렉토리 생성 (존재하지 않을 경우)
   * @param name 프로젝트 이름
   */
  ensureProject(name: string): Promise<void>;

  /**
   * 프로젝트 삭제
   * @param name 프로젝트 이름
   * @returns 삭제 성공 여부
   */
  deleteProject?(name: string): Promise<boolean>;

  /**
   * 프로젝트 이름 변경
   * @param oldName 기존 프로젝트 이름
   * @param newName 새 프로젝트 이름
   * @returns 변경 성공 여부
   */
  renameProject?(oldName: string, newName: string): Promise<boolean>;

  /**
   * 프로젝트 정보 조회
   * @param name 프로젝트 이름
   * @returns 프로젝트 메타데이터
   */
  getProjectInfo?(name: string): Promise<{
    name: string;
    fileCount: number;
    lastModified: Date;
    size: number;
  } | null>;
}
