/**
 * Tool interfaces and types
 */

export interface ToolResult {
  content: Array<{
    type: string;
    text: string;
  }>;
}

export interface FlowProjectArgs {
  project_name: string;
}

export interface PlanProjectArgs {
  plan_name?: string;
  description?: string;
}

export interface TaskManageArgs {
  action: string;
  args?: string[];
}

export interface BackupFileArgs {
  filepath: string;
  reason?: string;
}

export interface RestoreBackupArgs {
  backup_path: string;
  targetPath?: string;
}

export interface ListBackupsArgs {
  filename?: string;
}

export interface ExecuteCodeArgs {
  code: string;
  language?: string;
}

export interface RestartJsonReplArgs {
  reason?: string;
  keep_helpers?: boolean;
}

export interface TrackMistakeArgs {
  mistake_type: string;
  context?: string;
}

export interface AddBestPracticeArgs {
  practice: string;
  category?: string;
}


// Project Management Types
export interface ListProjectsParams {
  filter?: string;
}

export interface ListProjectsResponse {
  projects: ProjectInfo[];
}

export interface ProjectInfo {
  name: string;
  path: string;
  lastAccessed: string;
  status: ProjectStatus;
}

export enum ProjectStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  UNKNOWN = 'unknown'
}

export interface CreateProjectParams {
  name: string;
  path?: string;
  description?: string;
}

export interface CreateProjectResponse {
  success: boolean;
  project?: ProjectInfo;
  error?: string;
}

export interface SwitchProjectParams {
  projectName: string;
}

export interface SwitchProjectResponse {
  success: boolean;
  previousProject?: string;
  currentProject: string;
  context?: any;
}

export interface ArchiveProjectParams {
  projectName: string;
  reason?: string;
}

export interface ExportProjectParams {
  projectName: string;
  format?: 'json' | 'zip';
  includeLogs?: boolean;
}
