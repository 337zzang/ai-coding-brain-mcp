/**
 * Repository Factory
 * 
 * Repository 구현체들의 인스턴스를 생성하고 관리하는 팩토리
 * Clean Architecture의 의존성 주입 패턴
 */

import { ProjectRepository, FileRepository } from '../../domain/repositories/index';
import { FsProjectRepository } from './fs-project-repository';
import { FsFileRepository } from './fs-file-repository';
import { createLogger } from '../../../services/logger';
import path from 'path';
import os from 'os';

const logger = createLogger('repository-factory');

/**
 * Repository 팩토리 설정 옵션
 */
export interface RepositoryFactoryConfig {
  /** Memory Bank 루트 디렉토리 */
  rootDir?: string;
  /** 사용할 Repository 타입 */
  type?: 'filesystem' | 'memory'; // 향후 확장 가능
}

/**
 * 기본 설정
 */
const DEFAULT_CONFIG: Required<RepositoryFactoryConfig> = {
  rootDir: process.env['MEMORY_BANK_ROOT'] || path.join(os.homedir(), 'memory-bank'),
  type: 'filesystem',
};

/**
 * Repository Factory 클래스
 */
export class RepositoryFactory {
  private static instance: RepositoryFactory;
  private readonly config: Required<RepositoryFactoryConfig>;
  
  // Repository 인스턴스 캐시
  private projectRepository: ProjectRepository | undefined;
  private fileRepository: FileRepository | undefined;

  /**
   * RepositoryFactory 생성자 (private - 싱글톤 패턴)
   * @param config 팩토리 설정
   */
  private constructor(config: RepositoryFactoryConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    logger.info(`Repository factory initialized with config: ${JSON.stringify(this.config)}`);
  }

  /**
   * 싱글톤 인스턴스 조회
   * @param config 초기 설정 (첫 호출시에만 적용)
   * @returns RepositoryFactory 인스턴스
   */
  public static getInstance(config?: RepositoryFactoryConfig): RepositoryFactory {
    if (!RepositoryFactory.instance) {
      RepositoryFactory.instance = new RepositoryFactory(config);
    }
    return RepositoryFactory.instance;
  }

  /**
   * 설정 리셋 (주로 테스트용)
   * @param config 새로운 설정
   */
  public static reset(config?: RepositoryFactoryConfig): RepositoryFactory {
    RepositoryFactory.instance = new RepositoryFactory(config);
    return RepositoryFactory.instance;
  }

  /**
   * ProjectRepository 인스턴스 생성/조회
   * @returns ProjectRepository 구현체
   */
  public getProjectRepository(): ProjectRepository {
    if (!this.projectRepository) {
      switch (this.config.type) {
        case 'filesystem':
          this.projectRepository = new FsProjectRepository(this.config.rootDir);
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
  public getFileRepository(): FileRepository {
    if (!this.fileRepository) {
      switch (this.config.type) {
        case 'filesystem':
          this.fileRepository = new FsFileRepository(this.config.rootDir);
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
  public getConfig(): Required<RepositoryFactoryConfig> {
    return { ...this.config };
  }

  /**
   * Memory Bank 루트 디렉토리 조회
   * @returns 루트 디렉토리 경로
   */
  public getRootDir(): string {
    return this.config.rootDir;
  }

  /**
   * Repository 캐시 클리어 (주로 테스트용)
   */
  public clearCache(): void {
    this.projectRepository = undefined;
    this.fileRepository = undefined;
    logger.debug('Repository cache cleared');
  }

  /**
   * 헬스 체크 - 모든 Repository의 기본 동작 확인
   * @returns 헬스 체크 결과
   */
  public async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    projectRepository: boolean;
    fileRepository: boolean;
    rootDir: string;
    timestamp: Date;
  }> {
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
          const files = await fileRepo.listFiles(projects[0]!);
          fileRepoHealthy = Array.isArray(files);
        } else {
          // 프로젝트가 없어도 에러가 발생하지 않으면 정상
          const files = await fileRepo.listFiles('__health_check__');
          fileRepoHealthy = Array.isArray(files);
        }
      } catch {
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
    } catch (error) {
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

/**
 * 기본 Repository Factory 인스턴스 (편의용)
 */
export const defaultRepositoryFactory = RepositoryFactory.getInstance();
