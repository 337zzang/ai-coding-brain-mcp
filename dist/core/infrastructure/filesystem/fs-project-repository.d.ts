/**
 * FileSystem Project Repository Implementation
 *
 * 파일시스템 기반 프로젝트 관리 Repository 구현체
 * 기존 Memory Bank MCP에서 70% 재사용
 */
import { ProjectRepository } from '../../domain/repositories/project-repository';
import { Project } from '../../domain/entities/index';
/**
 * 파일시스템 기반 ProjectRepository 구현
 */
export declare class FsProjectRepository implements ProjectRepository {
    private readonly rootDir;
    /**
     * FsProjectRepository 생성자
     * @param rootDir 모든 프로젝트가 저장되는 루트 디렉토리
     */
    constructor(rootDir: string);
    /**
     * 루트 디렉토리 존재 확인 및 생성
     * @private
     */
    private ensureRootDirectory;
    /**
     * 프로젝트 경로 생성
     * @param projectName 프로젝트 이름
     * @returns 프로젝트 전체 경로
     * @private
     */
    private buildProjectPath;
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
     * 프로젝트 삭제 (확장 기능)
     * @param name 프로젝트 이름
     * @returns 삭제 성공 여부
     */
    deleteProject(name: string): Promise<boolean>;
    /**
     * 프로젝트 이름 변경 (확장 기능)
     * @param oldName 기존 프로젝트 이름
     * @param newName 새 프로젝트 이름
     * @returns 변경 성공 여부
     */
    renameProject(oldName: string, newName: string): Promise<boolean>;
    /**
     * 프로젝트 정보 조회 (확장 기능)
     * @param name 프로젝트 이름
     * @returns 프로젝트 메타데이터
     */
    getProjectInfo(name: string): Promise<{
        name: string;
        fileCount: number;
        lastModified: Date;
        size: number;
    } | null>;
}
//# sourceMappingURL=fs-project-repository.d.ts.map