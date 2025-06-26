/**
 * Git Handlers - AI Coding Brain MCP
 * Git 관련 MCP 도구 핸들러
 */

import { createLogger } from '../services/logger';

const logger = createLogger('git-handlers');

/**
 * Git 상태 확인
 */
export async function handleGitStatus(_args: any): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { execSync } = require('child_process');
        const path = require('path');
        
        // Python 스크립트 경로 설정
        const pythonPath = path.join(process.cwd(), 'python');
        
        const pythonCode = `
import sys
import os
import json

# Python 경로 추가
sys.path.insert(0, '${pythonPath.replace(/\\/g, '\\\\')}')

# Windows Git 경로 설정
if sys.platform == 'win32':
    git_paths = [
        r"C:\\Program Files\\Git\\cmd",
        r"C:\\Program Files\\Git\\bin"
    ]
    for git_path in git_paths:
        if os.path.exists(git_path) and git_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = git_path + ';' + os.environ.get('PATH', '')

from git_version_manager import GitVersionManager

git_manager = GitVersionManager(os.getcwd())
result = git_manager.git_status()

# 결과를 더 읽기 쉬운 형태로 변환
if result:
    message = f"현재 브랜치: {result.get('branch', 'unknown')}\\n"
    message += f"수정된 파일: {len(result.get('modified', []))}개\\n"
    message += f"스테이징된 파일: {len(result.get('staged', []))}개\\n"
    message += f"추적되지 않은 파일: {len(result.get('untracked', []))}개\\n"
    message += f"깨끗한 상태: {'예' if result.get('clean') else '아니오'}"
    
    output = {
        "success": True,
        "message": message,
        "data": result
    }
else:
    output = {
        "success": False,
        "message": "Git 상태를 가져올 수 없습니다."
    }

print(json.dumps(output, ensure_ascii=False))
`;
        
        const result = execSync(
            `python -c "${pythonCode}"`,
            { 
                encoding: 'utf8', 
                cwd: process.cwd(),
                shell: true,
                env: { ...process.env }
            }
        );
        
        const gitResult = JSON.parse(result.trim());
        
        if (gitResult.success) {
            return {
                content: [{
                    type: 'text',
                    text: gitResult.message
                }]
            };
        } else {
            throw new Error(gitResult.message);
        }
    } catch (error) {
        logger.error('Git status failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 상태 확인 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 스마트 커밋
 */
export async function handleGitCommitSmart(args: { message?: string; auto_add?: boolean }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { execSync } = require('child_process');
        const message = args.message ? `"${args.message}"` : 'None';
        const autoAdd = args.auto_add !== false;
        
        const pythonCode = `
from mcp_git_tools import git_commit_smart
result = git_commit_smart(${message}, ${autoAdd})
print(json.dumps(result, ensure_ascii=False))
`;
        
        const result = execSync(
            `python -c "import json; ${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: process.cwd(),
                shell: true  // Windows 호환성을 위해 추가
            }
        );
        
        const commitResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: commitResult.message || 'Git 커밋 완료'
            }]
        };
    } catch (error) {
        logger.error('Git commit failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 커밋 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 스마트 브랜치
 */
export async function handleGitBranchSmart(args: { branch_name?: string; base_branch?: string }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { execSync } = require('child_process');
        const branchName = args.branch_name ? `"${args.branch_name}"` : 'None';
        const baseBranch = args.base_branch || 'main';
        
        const pythonCode = `
from mcp_git_tools import git_branch_smart
result = git_branch_smart(${branchName}, "${baseBranch}")
print(json.dumps(result, ensure_ascii=False))
`;
        
        const result = execSync(
            `python -c "import json; ${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: process.cwd(),
                shell: true  // Windows 호환성을 위해 추가
            }
        );
        
        const branchResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: branchResult.message || 'Git 브랜치 생성 완료'
            }]
        };
    } catch (error) {
        logger.error('Git branch failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 브랜치 생성 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 스마트 롤백
 */
export async function handleGitRollbackSmart(args: { target?: string; safe_mode?: boolean }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { execSync } = require('child_process');
        const target = args.target ? `"${args.target}"` : 'None';
        const safeMode = args.safe_mode !== false;
        
        const pythonCode = `
from mcp_git_tools import git_rollback_smart
result = git_rollback_smart(${target}, ${safeMode})
print(json.dumps(result, ensure_ascii=False))
`;
        
        const result = execSync(
            `python -c "import json; ${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: process.cwd(),
                shell: true  // Windows 호환성을 위해 추가
            }
        );
        
        const rollbackResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: rollbackResult.message || 'Git 롤백 완료'
            }]
        };
    } catch (error) {
        logger.error('Git rollback failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 롤백 실패: ${error}`
            }]
        };
    }
}

/**
 * Git 푸시
 */
export async function handleGitPush(args: { remote?: string; branch?: string }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const { execSync } = require('child_process');
        const remote = args.remote || 'origin';
        const branch = args.branch ? `"${args.branch}"` : 'None';
        
        const pythonCode = `
from mcp_git_tools import git_push
result = git_push("${remote}", ${branch})
print(json.dumps(result, ensure_ascii=False))
`;
        
        const result = execSync(
            `python -c "import json; ${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: process.cwd(),
                shell: true  // Windows 호환성을 위해 추가
            }
        );
        
        const pushResult = JSON.parse(result.trim());
        
        return {
            content: [{
                type: 'text',
                text: pushResult.message || 'Git 푸시 완료'
            }]
        };
    } catch (error) {
        logger.error('Git push failed:', error);
        return {
            content: [{
                type: 'text',
                text: `Git 푸시 실패: ${error}`
            }]
        };
    }
}
