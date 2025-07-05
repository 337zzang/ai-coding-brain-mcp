/**
 * FileSystem Project Repository Implementation
 * 
 * 파일시스템 기반 프로젝트 관리 Repository 구현체
 * 기존 Memory Bank MCP에서 70% 재사용
 */

import fs from 'fs-extra';
import path from 'path';
import { ProjectRepository } from '../../domain/repositories/project-repository';
import { Project, ProjectUtils } from '../../domain/entities/index';
import { createLogger } from '../../../services/logger';

const logger = createLogger('fs-project-repository');

/**
 * 파일시스템 기반 ProjectRepository 구현
 */
export class FsProjectRepository implements ProjectRepository {
  /**
   * FsProjectRepository 생성자
   * @param rootDir 모든 프로젝트가 저장되는 루트 디렉토리
   */
  constructor(private readonly rootDir: string) {
    this.ensureRootDirectory();
  }

  /**
   * 루트 디렉토리 존재 확인 및 생성
   * @private
   */
  private async ensureRootDirectory(): Promise<void> {
    try {
      await fs.ensureDir(this.rootDir);
      logger.debug(`Root directory ensured: ${this.rootDir}`);
    } catch (error) {
      logger.error(`Failed to ensure root directory: ${this.rootDir}`, error);
      throw error;
    }
  }

  /**
   * 프로젝트 경로 생성
   * @param projectName 프로젝트 이름
   * @returns 프로젝트 전체 경로
   * @private
   */
  private buildProjectPath(projectName: string): string {
    const normalizedName = ProjectUtils.normalizeProjectName(projectName);
    return path.join(this.rootDir, normalizedName);
  }

  /**
   * 모든 프로젝트 목록 조회
   * @returns 프로젝트 배열
   */
  async listProjects(): Promise<Project[]> {
    try {
      logger.debug('Listing all projects');
      
      const entries = await fs.readdir(this.rootDir, { withFileTypes: true });
      const projects: Project[] = entries
        .filter((entry) => entry.isDirectory())
        .map((entry) => entry.name)
        .filter((name) => ProjectUtils.isValidProjectName(name));

      logger.info(`Found ${projects.length} projects`);
      return projects;
    } catch (error) {
      logger.error('Failed to list projects', error);
      throw new Error(`Failed to list projects: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 프로젝트 존재 여부 확인
   * @param name 프로젝트 이름
   * @returns 존재 여부
   */
  async projectExists(name: string): Promise<boolean> {
    try {
      if (!ProjectUtils.isValidProjectName(name)) {
        logger.warn(`Invalid project name: ${name}`);
        return false;
      }

      const projectPath = this.buildProjectPath(name);
      const exists = await fs.pathExists(projectPath);
      
      if (exists) {
        const stat = await fs.stat(projectPath);
        const isDirectory = stat.isDirectory();
        logger.debug(`Project ${name} exists: ${isDirectory}`);
        return isDirectory;
      }
      
      logger.debug(`Project ${name} does not exist`);
      return false;
    } catch (error) {
      logger.error(`Failed to check project existence: ${name}`, error);
      return false;
    }
  }

  /**
   * 프로젝트 디렉토리 생성 (존재하지 않을 경우)
   * @param name 프로젝트 이름
   */
  async ensureProject(name: string): Promise<void> {
    try {
      if (!ProjectUtils.isValidProjectName(name)) {
        throw new Error(`Invalid project name: ${name}`);
      }

      const projectPath = this.buildProjectPath(name);
      await fs.ensureDir(projectPath);
      
      logger.info(`Project ensured: ${name}`);
    } catch (error) {
      logger.error(`Failed to ensure project: ${name}`, error);
      throw new Error(`Failed to ensure project: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 프로젝트 삭제 (확장 기능)
   * @param name 프로젝트 이름
   * @returns 삭제 성공 여부
   */
  async deleteProject(name: string): Promise<boolean> {
    try {
      if (!ProjectUtils.isValidProjectName(name)) {
        logger.warn(`Invalid project name for deletion: ${name}`);
        return false;
      }

      const projectPath = this.buildProjectPath(name);
      const exists = await this.projectExists(name);
      
      if (!exists) {
        logger.warn(`Project does not exist for deletion: ${name}`);
        return false;
      }

      await fs.remove(projectPath);
      logger.info(`Project deleted: ${name}`);
      return true;
    } catch (error) {
      logger.error(`Failed to delete project: ${name}`, error);
      return false;
    }
  }

  /**
   * 프로젝트 이름 변경 (확장 기능)
   * @param oldName 기존 프로젝트 이름
   * @param newName 새 프로젝트 이름
   * @returns 변경 성공 여부
   */
  async renameProject(oldName: string, newName: string): Promise<boolean> {
    try {
      if (!ProjectUtils.isValidProjectName(oldName) || !ProjectUtils.isValidProjectName(newName)) {
        logger.warn(`Invalid project names for rename: ${oldName} -> ${newName}`);
        return false;
      }

      const oldPath = this.buildProjectPath(oldName);
      const newPath = this.buildProjectPath(newName);

      const oldExists = await this.projectExists(oldName);
      const newExists = await this.projectExists(newName);

      if (!oldExists) {
        logger.warn(`Source project does not exist for rename: ${oldName}`);
        return false;
      }

      if (newExists) {
        logger.warn(`Target project already exists for rename: ${newName}`);
        return false;
      }

      await fs.move(oldPath, newPath);
      logger.info(`Project renamed: ${oldName} -> ${newName}`);
      return true;
    } catch (error) {
      logger.error(`Failed to rename project: ${oldName} -> ${newName}`, error);
      return false;
    }
  }

  /**
   * 프로젝트 정보 조회 (확장 기능)
   * @param name 프로젝트 이름
   * @returns 프로젝트 메타데이터
   */
  async getProjectInfo(name: string): Promise<{
    name: string;
    fileCount: number;
    lastModified: Date;
    size: number;
  } | null> {
    try {
      if (!ProjectUtils.isValidProjectName(name)) {
        logger.warn(`Invalid project name for info: ${name}`);
        return null;
      }

      const exists = await this.projectExists(name);
      if (!exists) {
        logger.warn(`Project does not exist for info: ${name}`);
        return null;
      }

      const projectPath = this.buildProjectPath(name);
      const stat = await fs.stat(projectPath);
      const entries = await fs.readdir(projectPath, { withFileTypes: true });
      const fileCount = entries.filter(entry => entry.isFile()).length;

      // 디렉토리 크기 계산 (모든 파일 크기 합계)
      let totalSize = 0;
      for (const entry of entries) {
        if (entry.isFile()) {
          const filePath = path.join(projectPath, entry.name);
          const fileStat = await fs.stat(filePath);
          totalSize += fileStat.size;
        }
      }

      logger.debug(`Project info retrieved: ${name}`);
      return {
        name,
        fileCount,
        lastModified: stat.mtime,
        size: totalSize,
      };
    } catch (error) {
      logger.error(`Failed to get project info: ${name}`, error);
      return null;
    }
  }
}
