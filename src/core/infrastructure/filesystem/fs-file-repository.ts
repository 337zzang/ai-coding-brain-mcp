/**
 * FileSystem File Repository Implementation
 * 
 * 파일시스템 기반 파일 관리 Repository 구현체
 * 기존 Memory Bank MCP에서 70% 재사용
 */

import fs from 'fs-extra';
import path from 'path';
import { FileRepository } from '../../domain/repositories/file-repository';
import { File, FileUtils } from '../../domain/entities/index';
import { createLogger } from '../../../services/logger';

const logger = createLogger('fs-file-repository');

/**
 * 파일시스템 기반 FileRepository 구현
 */
export class FsFileRepository implements FileRepository {
  /**
   * FsFileRepository 생성자
   * @param rootDir 모든 프로젝트가 저장되는 루트 디렉토리
   */
  constructor(private readonly rootDir: string) {}

  /**
   * 프로젝트 경로 생성
   * @param projectName 프로젝트 이름
   * @returns 프로젝트 전체 경로
   * @private
   */
  private buildProjectPath(projectName: string): string {
    return path.join(this.rootDir, projectName);
  }

  /**
   * 파일 경로 생성
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 파일 전체 경로
   * @private
   */
  private buildFilePath(projectName: string, fileName: string): string {
    return path.join(this.rootDir, projectName, fileName);
  }

  /**
   * 프로젝트 내 모든 파일 목록 조회
   * @param projectName 프로젝트 이름
   * @returns 파일 이름 배열
   */
  async listFiles(projectName: string): Promise<File[]> {
    try {
      logger.debug(`Listing files in project: ${projectName}`);
      
      const projectPath = this.buildProjectPath(projectName);
      const projectExists = await fs.pathExists(projectPath);
      
      if (!projectExists) {
        logger.warn(`Project does not exist: ${projectName}`);
        return [];
      }

      const entries = await fs.readdir(projectPath, { withFileTypes: true });
      const files = entries
        .filter((entry) => entry.isFile())
        .map((entry) => entry.name)
        .filter((name) => FileUtils.isValidFileName(name));

      logger.info(`Found ${files.length} files in project: ${projectName}`);
      return files;
    } catch (error) {
      logger.error(`Failed to list files in project: ${projectName}`, error);
      throw new Error(`Failed to list files: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 파일 내용 로드
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 파일 내용 (파일이 없으면 null)
   */
  async loadFile(projectName: string, fileName: string): Promise<string | null> {
    try {
      if (!FileUtils.isValidFileName(fileName)) {
        logger.warn(`Invalid file name: ${fileName}`);
        return null;
      }

      logger.debug(`Loading file: ${projectName}/${fileName}`);
      
      const filePath = this.buildFilePath(projectName, fileName);
      const fileExists = await fs.pathExists(filePath);
      
      if (!fileExists) {
        logger.debug(`File does not exist: ${projectName}/${fileName}`);
        return null;
      }

      const content = await fs.readFile(filePath, 'utf-8');
      logger.info(`File loaded successfully: ${projectName}/${fileName} (${content.length} chars)`);
      return content;
    } catch (error) {
      logger.error(`Failed to load file: ${projectName}/${fileName}`, error);
      throw new Error(`Failed to load file: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 파일 작성 (생성 또는 덮어쓰기)
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @param content 파일 내용
   * @param force 기존 파일 덮어쓰기 여부 (기본값: false)
   * @returns 작성된 파일 내용 (실패시 null)
   */
  async writeFile(
    projectName: string,
    fileName: string,
    content: string,
    force: boolean = false
  ): Promise<File | null> {
    try {
      if (!FileUtils.isValidFileName(fileName)) {
        throw new Error(`Invalid file name: ${fileName}`);
      }

      logger.debug(`Writing file: ${projectName}/${fileName} (force: ${force})`);
      
      const projectPath = this.buildProjectPath(projectName);
      await fs.ensureDir(projectPath);

      const filePath = this.buildFilePath(projectName, fileName);
      const fileExists = await fs.pathExists(filePath);
      
      if (fileExists && !force) {
        logger.warn(`File already exists (use force=true to overwrite): ${projectName}/${fileName}`);
        return null;
      }

      await fs.writeFile(filePath, content, 'utf-8');
      logger.info(`File ${fileExists ? 'overwritten' : 'written'} successfully: ${projectName}/${fileName} (${content.length} chars)`);
      
      // 작성된 내용 반환
      return await this.loadFile(projectName, fileName);
    } catch (error) {
      logger.error(`Failed to write file: ${projectName}/${fileName}`, error);
      throw new Error(`Failed to write file: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 파일 존재 여부 확인 (확장 기능)
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 존재 여부
   */
  async fileExists(projectName: string, fileName: string): Promise<boolean> {
    try {
      if (!FileUtils.isValidFileName(fileName)) {
        logger.warn(`Invalid file name: ${fileName}`);
        return false;
      }

      const filePath = this.buildFilePath(projectName, fileName);
      const exists = await fs.pathExists(filePath);
      
      if (exists) {
        const stat = await fs.stat(filePath);
        const isFile = stat.isFile();
        logger.debug(`File ${projectName}/${fileName} exists: ${isFile}`);
        return isFile;
      }
      
      logger.debug(`File ${projectName}/${fileName} does not exist`);
      return false;
    } catch (error) {
      logger.error(`Failed to check file existence: ${projectName}/${fileName}`, error);
      return false;
    }
  }

  /**
   * 파일 삭제 (확장 기능)
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 삭제 성공 여부
   */
  async deleteFile(projectName: string, fileName: string): Promise<boolean> {
    try {
      if (!FileUtils.isValidFileName(fileName)) {
        logger.warn(`Invalid file name for deletion: ${fileName}`);
        return false;
      }

      const exists = await this.fileExists(projectName, fileName);
      if (!exists) {
        logger.warn(`File does not exist for deletion: ${projectName}/${fileName}`);
        return false;
      }

      const filePath = this.buildFilePath(projectName, fileName);
      await fs.remove(filePath);
      
      logger.info(`File deleted: ${projectName}/${fileName}`);
      return true;
    } catch (error) {
      logger.error(`Failed to delete file: ${projectName}/${fileName}`, error);
      return false;
    }
  }

  /**
   * 파일 이름 변경 (확장 기능)
   * @param projectName 프로젝트 이름
   * @param oldFileName 기존 파일 이름
   * @param newFileName 새 파일 이름
   * @returns 변경 성공 여부
   */
  async renameFile(
    projectName: string,
    oldFileName: string,
    newFileName: string
  ): Promise<boolean> {
    try {
      if (!FileUtils.isValidFileName(oldFileName) || !FileUtils.isValidFileName(newFileName)) {
        logger.warn(`Invalid file names for rename: ${oldFileName} -> ${newFileName}`);
        return false;
      }

      const oldPath = this.buildFilePath(projectName, oldFileName);
      const newPath = this.buildFilePath(projectName, newFileName);

      const oldExists = await this.fileExists(projectName, oldFileName);
      const newExists = await this.fileExists(projectName, newFileName);

      if (!oldExists) {
        logger.warn(`Source file does not exist for rename: ${projectName}/${oldFileName}`);
        return false;
      }

      if (newExists) {
        logger.warn(`Target file already exists for rename: ${projectName}/${newFileName}`);
        return false;
      }

      await fs.move(oldPath, newPath);
      logger.info(`File renamed: ${projectName}/${oldFileName} -> ${newFileName}`);
      return true;
    } catch (error) {
      logger.error(`Failed to rename file: ${projectName}/${oldFileName} -> ${newFileName}`, error);
      return false;
    }
  }

  /**
   * 파일 메타데이터 조회 (확장 기능)
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @returns 파일 메타데이터
   */
  async getFileMetadata(projectName: string, fileName: string): Promise<{
    name: string;
    size: number;
    lastModified: Date;
    encoding: string;
  } | null> {
    try {
      if (!FileUtils.isValidFileName(fileName)) {
        logger.warn(`Invalid file name for metadata: ${fileName}`);
        return null;
      }

      const exists = await this.fileExists(projectName, fileName);
      if (!exists) {
        logger.warn(`File does not exist for metadata: ${projectName}/${fileName}`);
        return null;
      }

      const filePath = this.buildFilePath(projectName, fileName);
      const stat = await fs.stat(filePath);

      logger.debug(`File metadata retrieved: ${projectName}/${fileName}`);
      return {
        name: fileName,
        size: stat.size,
        lastModified: stat.mtime,
        encoding: 'utf-8', // 현재는 UTF-8만 지원
      };
    } catch (error) {
      logger.error(`Failed to get file metadata: ${projectName}/${fileName}`, error);
      return null;
    }
  }

  /**
   * 파일 부분 편집 (특정 내용 찾아서 교체)
   * @param projectName 프로젝트 이름
   * @param fileName 파일 이름
   * @param oldContent 찾을 기존 내용
   * @param newContent 교체할 새 내용
   * @param expectedOccurrences 예상 교체 횟수 (기본값: 1)
   * @returns 편집 결과 정보
   */
  async editFile(
    projectName: string,
    fileName: string,
    oldContent: string,
    newContent: string,
    expectedOccurrences: number = 1
  ): Promise<{
    success: boolean;
    actualOccurrences: number;
    updatedContent: string | null;
    message: string;
  }> {
    try {
      if (!FileUtils.isValidFileName(fileName)) {
        return {
          success: false,
          actualOccurrences: 0,
          updatedContent: null,
          message: `Invalid file name: ${fileName}`,
        };
      }

      logger.debug(`Editing file: ${projectName}/${fileName}`);
      
      // 파일 존재 확인
      const exists = await this.fileExists(projectName, fileName);
      if (!exists) {
        return {
          success: false,
          actualOccurrences: 0,
          updatedContent: null,
          message: `File does not exist: ${projectName}/${fileName}`,
        };
      }

      // 원본 내용 로드
      const originalContent = await this.loadFile(projectName, fileName);
      if (originalContent === null) {
        return {
          success: false,
          actualOccurrences: 0,
          updatedContent: null,
          message: `Failed to load file content: ${projectName}/${fileName}`,
        };
      }

      // oldContent 검색 및 교체 횟수 계산
      const occurrences = (originalContent.split(oldContent).length - 1);
      
      if (occurrences === 0) {
        return {
          success: false,
          actualOccurrences: 0,
          updatedContent: null,
          message: `Content not found in file: "${oldContent.length > 50 ? oldContent.substring(0, 50) + '...' : oldContent}"`,
        };
      }

      // 예상 교체 횟수 검증
      if (expectedOccurrences > 0 && occurrences !== expectedOccurrences) {
        return {
          success: false,
          actualOccurrences: occurrences,
          updatedContent: null,
          message: `Expected ${expectedOccurrences} occurrences, but found ${occurrences}`,
        };
      }

      // 내용 교체
      const updatedContent = originalContent.replaceAll(oldContent, newContent);
      
      // 파일 업데이트
      const result = await this.writeFile(projectName, fileName, updatedContent, true);
      if (result === null) {
        return {
          success: false,
          actualOccurrences: occurrences,
          updatedContent: null,
          message: `Failed to update file: ${projectName}/${fileName}`,
        };
      }

      logger.info(`File edited successfully: ${projectName}/${fileName} (${occurrences} replacements)`);
      return {
        success: true,
        actualOccurrences: occurrences,
        updatedContent: result,
        message: `Successfully replaced ${occurrences} occurrence(s)`,
      };
    } catch (error) {
      logger.error(`Failed to edit file: ${projectName}/${fileName}`, error);
      return {
        success: false,
        actualOccurrences: 0,
        updatedContent: null,
        message: `Edit failed: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  }
}
