"use strict";
/**
 * Project Context Handlers
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleBuildProjectContext = handleBuildProjectContext;
const logger_1 = require("../utils/logger");
const child_process_1 = require("child_process");
const util_1 = require("util");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const execFileAsync = (0, util_1.promisify)(child_process_1.execFile);
/**
 * Get project root directory
 */
function getProjectRoot() {
    let projectRoot = process.cwd();
    // ai-coding-brain-mcp 프로젝트 디렉토리 찾기
    if (!projectRoot.includes('ai-coding-brain-mcp')) {
        // 알려진 위치에서 찾기
        const possiblePaths = [
            'C:\\Users\\Administrator\\Desktop\\ai-coding-brain-mcp',
            path.join(process.env['USERPROFILE'] || '', 'Desktop', 'ai-coding-brain-mcp'),
            path.join(process.env['USERPROFILE'] || '', 'Documents', 'ai-coding-brain-mcp')
        ];
        for (const possiblePath of possiblePaths) {
            if (fs.existsSync(path.join(possiblePath, '.ai-brain.config.json'))) {
                projectRoot = possiblePath;
                break;
            }
        }
    }
    return projectRoot;
}
/**
 * Get Python path from config
 */
function getPythonPath() {
    const configPath = path.join(getProjectRoot(), '.ai-brain.config.json');
    if (fs.existsSync(configPath)) {
        try {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            return config.python?.path || 'python';
        }
        catch (e) {
            logger_1.logger.warn('Failed to read config, using default python path');
        }
    }
    return 'python';
}
/**
 * Get Python environment
 */
function getPythonEnv() {
    const projectRoot = getProjectRoot();
    return {
        ...process.env,
        PYTHONPATH: path.join(projectRoot, 'python'),
        PYTHONIOENCODING: 'utf-8',
        PYTHONDONTWRITEBYTECODE: '1',
        PYTHONUNBUFFERED: '1'
    };
}
/**
 * Build project context handler
 */
async function handleBuildProjectContext(args) {
    try {
        const { update_readme = true, update_context = true, include_stats = true, include_file_directory = false } = args;
        const pythonPath = getPythonPath();
        const projectRoot = getProjectRoot();
        // Python 스크립트 내용
        const scriptContent = `
import sys
import os
sys.path.insert(0, r'${projectRoot.replace(/\\/g, '\\\\')}\\python')
os.chdir(r'${projectRoot.replace(/\\/g, '\\\\')}')

# 프로젝트 컨텍스트 문서 생성
from project_context_builder import ProjectContextBuilder

builder = ProjectContextBuilder()
project_name = os.path.basename(os.getcwd())

results = []

# README.md 업데이트
if ${update_readme ? 'True' : 'False'}:
    try:
        readme_content = builder.build_readme(project_name)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        results.append("✅ README.md 업데이트 완료")
    except Exception as e:
        results.append(f"❌ README.md 업데이트 실패: {str(e)}")

# PROJECT_CONTEXT.md 업데이트
if ${update_context ? 'True' : 'False'}:
    try:
        context_content = builder.build_project_context(
            include_stats=${include_stats ? 'True' : 'False'}
        )
        with open('PROJECT_CONTEXT.md', 'w', encoding='utf-8') as f:
            f.write(context_content)
        results.append("✅ PROJECT_CONTEXT.md 업데이트 완료")
    except Exception as e:
        results.append(f"❌ PROJECT_CONTEXT.md 업데이트 실패: {str(e)}")

# file_directory.md 생성
if ${include_file_directory ? 'True' : 'False'}:
    try:
        # 간단한 파일 목록 생성
        import glob
        
        directory_content = "# 📂 파일 디렉토리 구조\\n\\n"
        directory_content += "\`\`\`\\n"
        directory_content += f"{project_name}/\\n"
        
        # 파일 목록 생성
        files = []
        for ext in ['*.py', '*.ts', '*.js', '*.json', '*.md']:
            files.extend(glob.glob(f'**/{ext}', recursive=True))
        
        for f in sorted(set(files))[:100]:  # 최대 100개 파일
            directory_content += f"├── {f}\\n"
        if len(files) > 100:
            directory_content += f"└── ... ({len(files) - 100} more files)\\n"
        
        directory_content += "\`\`\`\\n"
        
        with open('file_directory.md', 'w', encoding='utf-8') as f:
            f.write(directory_content)
        results.append("✅ file_directory.md 생성 완료")
    except Exception as e:
        results.append(f"❌ file_directory.md 생성 실패: {str(e)}")

# 결과 출력
for result in results:
    print(result)

if not results:
    print("⚠️ 처리할 작업이 없습니다.")
`;
        const { stdout, stderr } = await execFileAsync(pythonPath, ['-c', scriptContent], {
            env: getPythonEnv(),
            cwd: projectRoot,
            windowsHide: true
        });
        if (stderr) {
            logger_1.logger.warn(`Python stderr: ${stderr}`);
        }
        return {
            content: [{
                    type: 'text',
                    text: stdout.trim() || '✅ 프로젝트 컨텍스트 빌드 완료'
                }]
        };
    }
    catch (error) {
        logger_1.logger.error('Build project context failed:', error);
        return {
            content: [{
                    type: 'text',
                    text: `❌ Build failed: ${error.message}`
                }]
        };
    }
}
//# sourceMappingURL=project-handlers.js.map