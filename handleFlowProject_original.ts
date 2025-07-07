export async function handleFlowProject(params: { project_name: string }): Promise<ToolResult> {
    const code = `
# 개선된 flow_project 핸들러 - 명시적 에러 처리
import sys
import os
import json
import traceback
from pathlib import Path

project_name = "${params.project_name}"
result = {
    "success": False,
    "project_name": project_name,
    "error": None,
    "details": {}
}