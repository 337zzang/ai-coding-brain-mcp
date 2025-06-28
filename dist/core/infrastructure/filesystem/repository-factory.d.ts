/**
 * Repository Factory
 *
 * Repository 구현체들의 인스턴스를 생성하고 관리하는 팩토리
 * Clean Architecture의 의존성 주입 패턴
 */
import { ProjectRepository, FileRepository } from '../../domain/repositories/index';
/**
 * Repository 팩토리 설정 옵션
 */
export interface RepositoryFactoryConfig {
    /** Memory Bank 루트 디렉토리 */
    rootDir?: string;
    /** 사용할 Repository 타입 */
    type?: 'filesystem' | 'memory';
}
/**
 * Repository Factory 클래스
 */
export declare class RepositoryFactory {
    private static instance;
    private readonly config;
    private projectRepository;
    private fileRepository;
    /**
     * RepositoryFactory 생성자 (private - 싱글톤 패턴)
     * @param config 팩토리 설정
     */
    private constructor();
    /**
     * 싱글톤 인스턴스 조회
     * @param config 초기 설정 (첫 호출시에만 적용)
     * @returns RepositoryFactory 인스턴스
     */
    static getInstance(config?: RepositoryFactoryConfig): RepositoryFactory;
    /**
     * 설정 리셋 (주로 테스트용)
     * @param config 새로운 설정
     */
    static reset(config?: RepositoryFactoryConfig): RepositoryFactory;
    /**
     * ProjectRepository 인스턴스 생성/조회
     * @returns ProjectRepository 구현체
     */
    getProjectRepository(): ProjectRepository;
    /**
     * FileRepository 인스턴스 생성/조회
     * @returns FileRepository 구현체
     */
    getFileRepository(): FileRepository;
    /**
     * 현재 설정 조회
     * @returns 팩토리 설정
     */
    getConfig(): Required<RepositoryFactoryConfig>;
    /**
     * Memory Bank 루트 디렉토리 조회
     * @returns 루트 디렉토리 경로
     */
    getRootDir(): string;
    /**
     * Repository 캐시 클리어 (주로 테스트용)
     */
    clearCache(): void;
    /**
     * 헬스 체크 - 모든 Repository의 기본 동작 확인
     * @returns 헬스 체크 결과
     */
    healthCheck(): Promise<{
        status: 'healthy' | 'unhealthy';
        projectRepository: boolean;
        fileRepository: boolean;
        rootDir: string;
        timestamp: Date;
    }>;
}
/**
 * 기본 Repository Factory 인스턴스 (편의용)
 */
export declare const defaultRepositoryFactory: RepositoryFactory;
//# sourceMappingURL=repository-factory.d.ts.map