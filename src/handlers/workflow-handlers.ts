import { ToolResult } from '../types/tool-interfaces';
import { logger } from '../services/logger';
// import { getActiveReplSession } from './repl-session-manager'; // Not exported

interface FlowProjectResult {
    success: boolean;
    project_name?: string;
    path?: string;
    git_branch?: string;
    workflow_status?: any;
    workflow_integration?: {
        enabled: boolean;
        events?: any[];
        current_state?: string;
        active_plan?: string | null;
        plans_count?: number;
        sync_status?: string;
    };
    briefing?: string | null;
    timestamp?: string;
    error?: string;
    details?: any;
}
// 기타 워크플로우 관련 핸들러들...
