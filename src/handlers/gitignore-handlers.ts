/**
 * Gitignore 관련 핸들러
 */

import { execSync } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

/**
 * 프로젝트 분석하여 .gitignore 제안
 */
export async function handleGitignoreAnalyze(): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const projectRoot = process.cwd();
        const scriptPath = path.join(projectRoot, 'python', 'gitignore_manager.py');
        
        if (!fs.existsSync(scriptPath)) {
            throw new Error('gitignore_manager.py를 찾을 수 없습니다.');
        }
        
        const pythonCode = `
import json
from gitignore_manager import get_gitignore_manager

manager = get_gitignore_manager()
suggestions = manager.analyze_project()

# 결과 포맷팅
result = {
    "found": bool(suggestions),
    "categories": {}
}

for category, patterns in suggestions.items():
    result["categories"][category] = patterns

print(json.dumps(result, ensure_ascii=False))
`;
        
        const output = execSync(
            `python -c "${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: projectRoot,
                shell: true
            }
        );
        
        const result = JSON.parse(output.trim());
        
        if (!result.found) {
            return {
                content: [{
                    type: 'text',
                    text: '프로젝트에서 .gitignore에 추가할 만한 파일/폴더를 찾지 못했습니다.'
                }]
            };
        }
        
        let text = '🔍 프로젝트 분석 결과\n\n';
        text += '.gitignore에 추가하면 좋을 패턴들:\n\n';
        
        for (const [category, patterns] of Object.entries(result.categories)) {
            text += `**${category}**\n`;
            for (const pattern of patterns as string[]) {
                text += `- ${pattern}\n`;
            }
            text += '\n';
        }
        
        return {
            content: [{
                type: 'text',
                text: text
            }]
        };
        
    } catch (error: any) {
        return {
            content: [{
                type: 'text',
                text: `오류 발생: ${error.message}`
            }]
        };
    }
}

/**
 * .gitignore 파일 업데이트
 */
export async function handleGitignoreUpdate(args: { patterns: string[]; category?: string }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const projectRoot = process.cwd();
        const patterns = JSON.stringify(args.patterns);
        const category = args.category ? `"${args.category}"` : 'None';
        
        const pythonCode = `
import json
from gitignore_manager import get_gitignore_manager

manager = get_gitignore_manager()
result = manager.update_gitignore(${patterns}, ${category})

print(json.dumps(result, ensure_ascii=False))
`;
        
        const output = execSync(
            `python -c "${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: projectRoot,
                shell: true
            }
        );
        
        const result = JSON.parse(output.trim());
        
        let text = result.message + '\n\n';
        
        if (result.added && result.added.length > 0) {
            text += '✅ 추가된 패턴:\n';
            for (const pattern of result.added) {
                text += `- ${pattern}\n`;
            }
        }
        
        if (result.existing && result.existing.length > 0) {
            text += '\n⚠️ 이미 존재하는 패턴:\n';
            for (const pattern of result.existing) {
                text += `- ${pattern}\n`;
            }
        }
        
        return {
            content: [{
                type: 'text',
                text: text
            }]
        };
        
    } catch (error: any) {
        return {
            content: [{
                type: 'text',
                text: `오류 발생: ${error.message}`
            }]
        };
    }
}

/**
 * 새로운 .gitignore 파일 생성
 */
export async function handleGitignoreCreate(args: { categories?: string[] }): Promise<{ content: Array<{ type: string; text: string }> }> {
    try {
        const projectRoot = process.cwd();
        const categories = args.categories ? JSON.stringify(args.categories) : 'None';
        
        const pythonCode = `
import json
from gitignore_manager import get_gitignore_manager

manager = get_gitignore_manager()
result = manager.create_gitignore(${categories})

print(json.dumps(result, ensure_ascii=False))
`;
        
        const output = execSync(
            `python -c "${pythonCode.replace(/"/g, '\\"')}"`,
            { 
                encoding: 'utf8', 
                cwd: projectRoot,
                shell: true
            }
        );
        
        const result = JSON.parse(output.trim());
        
        if (!result.success) {
            return {
                content: [{
                    type: 'text',
                    text: result.message
                }]
            };
        }
        
        let text = result.message + '\n\n';
        text += '📝 포함된 카테고리:\n';
        for (const category of result.categories) {
            text += `- ${category}\n`;
        }
        
        return {
            content: [{
                type: 'text',
                text: text
            }]
        };
        
    } catch (error: any) {
        return {
            content: [{
                type: 'text',
                text: `오류 발생: ${error.message}`
            }]
        };
    }
}
