import { createLogger } from '../utils/logger';
import { promises as fs } from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const logger = createLogger('build-handler');

export interface BuildProjectContextArgs {
  update_readme?: boolean;
  update_context?: boolean;
  include_stats?: boolean;
  include_file_directory?: boolean;
}

export async function handleBuildProjectContext(args: BuildProjectContextArgs): Promise<any> {
  const {
    update_readme = true,
    update_context = true,
    include_stats = true,
    include_file_directory = false
  } = args;

  try {
    logger.info('🏗️ 프로젝트 컨텍스트 문서 빌드 시작...');
    
    // Python 스크립트 경로
    const scriptPath = path.join(__dirname, '..', '..', 'python', 'project_context_builder.py');
    
    // Python 스크립트 실행
    const pythonArgs = [
      scriptPath,
      '--update-readme', update_readme ? 'true' : 'false',
      '--update-context', update_context ? 'true' : 'false',
      '--include-stats', include_stats ? 'true' : 'false'
    ,
      '--include-file-directory', include_file_directory ? 'true' : 'false'
    ];
    
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', pythonArgs, {
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
        } catch (e) {
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
    
  } catch (error) {
    logger.error(`❌ 빌드 실패: ${error}`);
    throw error;
  }
}

async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}
