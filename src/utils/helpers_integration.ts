// AI Coding Brain MCP - Helpers Integration for TypeScript
// Generated: 2025-07-15 07:04:24

// @ts-ignore
import { PythonShell } from 'python-shell';
import * as path from 'path';
import * as fs from 'fs';

export class HelpersIntegration {
    private pythonPath: string;
    private helpersPath: string;

    constructor() {
        this.pythonPath = process.env.PYTHON_PATH || 'python';
        this.helpersPath = path.join(__dirname, '../utils/improved_helpers.py');
    }

    async flowProject(projectName: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const options = {
                mode: 'json' as const,
                pythonPath: this.pythonPath,
                pythonOptions: ['-u'],
                scriptPath: path.dirname(this.helpersPath),
                args: ['flow_project', projectName]
            };

            PythonShell.run(path.basename(this.helpersPath), options, (err: any, results: any) => {
                if (err) reject(err);
                else resolve(results?.[0]);
            });
        });
    }

    async getCurrentProject(): Promise<string | null> {
        const contextPath = path.join(process.cwd(), 'memory', 'context.json');
        if (fs.existsSync(contextPath)) {
            const context = JSON.parse(fs.readFileSync(contextPath, 'utf-8'));
            return context.current_project || null;
        }
        return null;
    }
}

export const helpers = new HelpersIntegration();
