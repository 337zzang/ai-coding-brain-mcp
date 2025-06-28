"use strict";
/**
 * FileSystem Project Repository Implementation
 *
 * 파일시스템 기반 프로젝트 관리 Repository 구현체
 * 기존 Memory Bank MCP에서 70% 재사용
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FsProjectRepository = void 0;
const fs_extra_1 = __importDefault(require("fs-extra"));
const path_1 = __importDefault(require("path"));
const index_1 = require("../../domain/entities/index");
const logger_1 = require("../../../services/logger");
const logger = (0, logger_1.createLogger)('fs-project-repository');
/**
 * 파일시스템 기반 ProjectRepository 구현
 */
class FsProjectRepository {
    /**
     * FsProjectRepository 생성자
     * @param rootDir 모든 프로젝트가 저장되는 루트 디렉토리
     */
    constructor(rootDir) {
        this.rootDir = rootDir;
        this.ensureRootDirectory();
    }
    /**
     * 루트 디렉토리 존재 확인 및 생성
     * @private
     */
    async ensureRootDirectory() {
        try {
            await fs_extra_1.default.ensureDir(this.rootDir);
            logger.debug(`Root directory ensured: ${this.rootDir}`);
        }
        catch (error) {
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
    buildProjectPath(projectName) {
        const normalizedName = index_1.ProjectUtils.normalizeProjectName(projectName);
        return path_1.default.join(this.rootDir, normalizedName);
    }
    /**
     * 모든 프로젝트 목록 조회
     * @returns 프로젝트 배열
     */
    async listProjects() {
        try {
            logger.debug('Listing all projects');
            const entries = await fs_extra_1.default.readdir(this.rootDir, { withFileTypes: true });
            const projects = entries
                .filter((entry) => entry.isDirectory())
                .map((entry) => entry.name)
                .filter((name) => index_1.ProjectUtils.isValidProjectName(name));
            logger.info(`Found ${projects.length} projects`);
            return projects;
        }
        catch (error) {
            logger.error('Failed to list projects', error);
            throw new Error(`Failed to list projects: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * 프로젝트 존재 여부 확인
     * @param name 프로젝트 이름
     * @returns 존재 여부
     */
    async projectExists(name) {
        try {
            if (!index_1.ProjectUtils.isValidProjectName(name)) {
                logger.warn(`Invalid project name: ${name}`);
                return false;
            }
            const projectPath = this.buildProjectPath(name);
            const exists = await fs_extra_1.default.pathExists(projectPath);
            if (exists) {
                const stat = await fs_extra_1.default.stat(projectPath);
                const isDirectory = stat.isDirectory();
                logger.debug(`Project ${name} exists: ${isDirectory}`);
                return isDirectory;
            }
            logger.debug(`Project ${name} does not exist`);
            return false;
        }
        catch (error) {
            logger.error(`Failed to check project existence: ${name}`, error);
            return false;
        }
    }
    /**
     * 프로젝트 디렉토리 생성 (존재하지 않을 경우)
     * @param name 프로젝트 이름
     */
    async ensureProject(name) {
        try {
            if (!index_1.ProjectUtils.isValidProjectName(name)) {
                throw new Error(`Invalid project name: ${name}`);
            }
            const projectPath = this.buildProjectPath(name);
            await fs_extra_1.default.ensureDir(projectPath);
            logger.info(`Project ensured: ${name}`);
        }
        catch (error) {
            logger.error(`Failed to ensure project: ${name}`, error);
            throw new Error(`Failed to ensure project: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * 프로젝트 삭제 (확장 기능)
     * @param name 프로젝트 이름
     * @returns 삭제 성공 여부
     */
    async deleteProject(name) {
        try {
            if (!index_1.ProjectUtils.isValidProjectName(name)) {
                logger.warn(`Invalid project name for deletion: ${name}`);
                return false;
            }
            const projectPath = this.buildProjectPath(name);
            const exists = await this.projectExists(name);
            if (!exists) {
                logger.warn(`Project does not exist for deletion: ${name}`);
                return false;
            }
            await fs_extra_1.default.remove(projectPath);
            logger.info(`Project deleted: ${name}`);
            return true;
        }
        catch (error) {
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
    async renameProject(oldName, newName) {
        try {
            if (!index_1.ProjectUtils.isValidProjectName(oldName) || !index_1.ProjectUtils.isValidProjectName(newName)) {
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
            await fs_extra_1.default.move(oldPath, newPath);
            logger.info(`Project renamed: ${oldName} -> ${newName}`);
            return true;
        }
        catch (error) {
            logger.error(`Failed to rename project: ${oldName} -> ${newName}`, error);
            return false;
        }
    }
    /**
     * 프로젝트 정보 조회 (확장 기능)
     * @param name 프로젝트 이름
     * @returns 프로젝트 메타데이터
     */
    async getProjectInfo(name) {
        try {
            if (!index_1.ProjectUtils.isValidProjectName(name)) {
                logger.warn(`Invalid project name for info: ${name}`);
                return null;
            }
            const exists = await this.projectExists(name);
            if (!exists) {
                logger.warn(`Project does not exist for info: ${name}`);
                return null;
            }
            const projectPath = this.buildProjectPath(name);
            const stat = await fs_extra_1.default.stat(projectPath);
            const entries = await fs_extra_1.default.readdir(projectPath, { withFileTypes: true });
            const fileCount = entries.filter(entry => entry.isFile()).length;
            // 디렉토리 크기 계산 (모든 파일 크기 합계)
            let totalSize = 0;
            for (const entry of entries) {
                if (entry.isFile()) {
                    const filePath = path_1.default.join(projectPath, entry.name);
                    const fileStat = await fs_extra_1.default.stat(filePath);
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
        }
        catch (error) {
            logger.error(`Failed to get project info: ${name}`, error);
            return null;
        }
    }
}
exports.FsProjectRepository = FsProjectRepository;
//# sourceMappingURL=fs-project-repository.js.map