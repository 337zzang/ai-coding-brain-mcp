"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleBuildProjectContext = handleBuildProjectContext;
const logger_1 = require("../utils/logger");
const fs_1 = require("fs");
const path_1 = __importDefault(require("path"));
const child_process_1 = require("child_process");
const logger = (0, logger_1.createLogger)('build-handler');
async function handleBuildProjectContext(args) {
    const { update_readme = true, update_context = true, include_stats = true, include_file_directory = false } = args;
    try {
        logger.info('🏗️ 프로젝트 컨텍스트 문서 빌드 시작...');
        // Python 스크립트 경로
        const scriptPath = path_1.default.join(__dirname, '..', '..', 'python', 'project_context_builder.py');
        // Python 스크립트 실행
        const pythonArgs = [
            scriptPath,
            '--update-readme', update_readme ? 'true' : 'false',
            '--update-context', update_context ? 'true' : 'false',
            '--include-stats', include_stats ? 'true' : 'false',
            '--include-file-directory', include_file_directory ? 'true' : 'false'
        ];
        return new Promise((resolve, reject) => {
            const pythonProcess = (0, child_process_1.spawn)('python', pythonArgs, {
                cwd: process.cwd(),
                env: process.env
            });
            let stdout = '';
            let stderr = '';
            pythonProcess.stdout.on('data', (data) => {
                const output = data.toString();
                stdout += output;
                logger.info(output.trim());
            });
            pythonProcess.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            pythonProcess.on('close', async (code) => {
                if (code !== 0) {
                    reject(new Error(`Build process failed with code ${code}: ${stderr}`));
                    return;
                }
                // 생성된 문서 확인
                const docs = [];
                if (update_readme && await fileExists('README.md')) {
                    docs.push('README.md');
                }
                if (update_context && await fileExists('PROJECT_CONTEXT.md')) {
                    docs.push('PROJECT_CONTEXT.md');
                }
                // file_directory.md도 업데이트 (기존 flow 로직 활용)
                try {
                    const { updateFileDirectory } = require('./workflow-handlers');
                    await updateFileDirectory(process.cwd());
                    docs.push('file_directory.md');
                }
                catch (e) {
                    logger.warn(`⚠️ file_directory.md 업데이트 실패: ${e instanceof Error ? e.message : String(e)}`);
                }
                resolve({
                    success: true,
                    message: `✅ 프로젝트 컨텍스트 문서 빌드 완료`,
                    documents: docs,
                    output: stdout
                });
            });
        });
    }
    catch (error) {
        logger.error(`❌ 빌드 실패: ${error}`);
        throw error;
    }
}
async function fileExists(filePath) {
    try {
        await fs_1.promises.access(filePath);
        return true;
    }
    catch {
        return false;
    }
}
//# sourceMappingURL=build-handler.js.map