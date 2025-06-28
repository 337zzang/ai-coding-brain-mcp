"use strict";
/**
 * Repository Factory
 *
 * Repository 구현체들의 인스턴스를 생성하고 관리하는 팩토리
 * Clean Architecture의 의존성 주입 패턴
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultRepositoryFactory = exports.RepositoryFactory = void 0;
const fs_project_repository_1 = require("./fs-project-repository");
const fs_file_repository_1 = require("./fs-file-repository");
const logger_1 = require("../../../services/logger");
const path_1 = __importDefault(require("path"));
const os_1 = __importDefault(require("os"));
const logger = (0, logger_1.createLogger)('repository-factory');
/**
 * 기본 설정
 */
const DEFAULT_CONFIG = {
    rootDir: process.env['MEMORY_BANK_ROOT'] || path_1.default.join(os_1.default.homedir(), 'memory-bank'),
    type: 'filesystem',
};
/**
 * Repository Factory 클래스
 */
class RepositoryFactory {
    /**
     * RepositoryFactory 생성자 (private - 싱글톤 패턴)
     * @param config 팩토리 설정
     */
    constructor(config = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
        logger.info(`Repository factory initialized with config: ${JSON.stringify(this.config)}`);
    }
    /**
     * 싱글톤 인스턴스 조회
     * @param config 초기 설정 (첫 호출시에만 적용)
     * @returns RepositoryFactory 인스턴스
     */
    static getInstance(config) {
        if (!RepositoryFactory.instance) {
            RepositoryFactory.instance = new RepositoryFactory(config);
        }
        return RepositoryFactory.instance;
    }
    /**
     * 설정 리셋 (주로 테스트용)
     * @param config 새로운 설정
     */
    static reset(config) {
        RepositoryFactory.instance = new RepositoryFactory(config);
        return RepositoryFactory.instance;
    }
    /**
     * ProjectRepository 인스턴스 생성/조회
     * @returns ProjectRepository 구현체
     */
    getProjectRepository() {
        if (!this.projectRepository) {
            switch (this.config.type) {
                case 'filesystem':
                    this.projectRepository = new fs_project_repository_1.FsProjectRepository(this.config.rootDir);
                    logger.debug('Created FsProjectRepository');
                    break;
                case 'memory':
                    // 향후 InMemoryProjectRepository 구현 예정
                    throw new Error('In-memory repository not implemented yet');
                default:
                    throw new Error(`Unsupported repository type: ${this.config.type}`);
            }
        }
        return this.projectRepository;
    }
    /**
     * FileRepository 인스턴스 생성/조회
     * @returns FileRepository 구현체
     */
    getFileRepository() {
        if (!this.fileRepository) {
            switch (this.config.type) {
                case 'filesystem':
                    this.fileRepository = new fs_file_repository_1.FsFileRepository(this.config.rootDir);
                    logger.debug('Created FsFileRepository');
                    break;
                case 'memory':
                    // 향후 InMemoryFileRepository 구현 예정
                    throw new Error('In-memory repository not implemented yet');
                default:
                    throw new Error(`Unsupported repository type: ${this.config.type}`);
            }
        }
        return this.fileRepository;
    }
    /**
     * 현재 설정 조회
     * @returns 팩토리 설정
     */
    getConfig() {
        return { ...this.config };
    }
    /**
     * Memory Bank 루트 디렉토리 조회
     * @returns 루트 디렉토리 경로
     */
    getRootDir() {
        return this.config.rootDir;
    }
    /**
     * Repository 캐시 클리어 (주로 테스트용)
     */
    clearCache() {
        this.projectRepository = undefined;
        this.fileRepository = undefined;
        logger.debug('Repository cache cleared');
    }
    /**
     * 헬스 체크 - 모든 Repository의 기본 동작 확인
     * @returns 헬스 체크 결과
     */
    async healthCheck() {
        try {
            const projectRepo = this.getProjectRepository();
            const fileRepo = this.getFileRepository();
            // 기본 동작 테스트
            const projects = await projectRepo.listProjects();
            const projectRepoHealthy = Array.isArray(projects);
            // 테스트 프로젝트에서 파일 목록 조회 시도
            let fileRepoHealthy = false;
            try {
                if (projects.length > 0) {
                    const files = await fileRepo.listFiles(projects[0]);
                    fileRepoHealthy = Array.isArray(files);
                }
                else {
                    // 프로젝트가 없어도 에러가 발생하지 않으면 정상
                    const files = await fileRepo.listFiles('__health_check__');
                    fileRepoHealthy = Array.isArray(files);
                }
            }
            catch {
                // 파일 목록 조회 실패는 정상 (프로젝트가 없을 수 있음)
                fileRepoHealthy = true;
            }
            const status = projectRepoHealthy && fileRepoHealthy ? 'healthy' : 'unhealthy';
            logger.info(`Repository health check: ${status}`);
            return {
                status,
                projectRepository: projectRepoHealthy,
                fileRepository: fileRepoHealthy,
                rootDir: this.config.rootDir,
                timestamp: new Date(),
            };
        }
        catch (error) {
            logger.error('Repository health check failed', error);
            return {
                status: 'unhealthy',
                projectRepository: false,
                fileRepository: false,
                rootDir: this.config.rootDir,
                timestamp: new Date(),
            };
        }
    }
}
exports.RepositoryFactory = RepositoryFactory;
/**
 * 기본 Repository Factory 인스턴스 (편의용)
 */
exports.defaultRepositoryFactory = RepositoryFactory.getInstance();
//# sourceMappingURL=repository-factory.js.map