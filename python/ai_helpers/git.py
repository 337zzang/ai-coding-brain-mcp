"""Git 관련 헬퍼 함수들"""

from typing import Dict, Any, List, Optional, Union
from .decorators import track_operation


@track_operation('git', 'status')
def git_status() -> Dict[str, Any]:
    """Git 저장소 상태 확인
    
    Returns:
        dict: 상태 정보 딕셔너리
            - success: 성공 여부
            - branch: 현재 브랜치
            - modified: 수정된 파일 목록
            - staged: 스테이징된 파일 목록
            - untracked: 추적되지 않는 파일 목록
            - clean: 깨끗한 상태 여부
    """
    try:
        from git import Repo
        repo = Repo('.')
        
        # 브랜치 정보
        branch = repo.active_branch.name
        
        # 변경된 파일들
        modified = [item.a_path for item in repo.index.diff(None)]
        staged = [item.a_path for item in repo.index.diff('HEAD')]
        untracked = repo.untracked_files
        
        return {
            'success': True,
            'branch': branch,
            'modified': modified,
            'staged': staged,
            'untracked': untracked,
            'clean': len(modified) == 0 and len(staged) == 0 and len(untracked) == 0
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@track_operation('git', 'add')
def git_add(files: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
    """파일을 스테이징 영역에 추가
    
    Args:
        files: 추가할 파일 (None이면 모든 파일)
    
    Returns:
        dict: 결과 정보
    """
    try:
        from git import Repo
        repo = Repo('.')
        
        if files is None:
            repo.git.add(A=True)  # 모든 파일 추가
        elif isinstance(files, str):
            repo.index.add([files])
        elif isinstance(files, list):
            repo.index.add(files)
            
        return {'success': True, 'message': f"파일 추가됨: {files or '모든 파일'}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@track_operation('git', 'commit')
def git_commit(message: str, auto_add: bool = False) -> Dict[str, Any]:
    """변경사항 커밋
    
    Args:
        message: 커밋 메시지
        auto_add: 커밋 전 자동으로 모든 파일 추가 여부
    
    Returns:
        dict: 결과 정보
    """
    try:
        from git import Repo
        repo = Repo('.')
        
        if auto_add:
            repo.git.add(A=True)
            
        # 커밋할 내용이 있는지 확인
        if repo.is_dirty() or len(repo.index.diff("HEAD")) > 0:
            repo.index.commit(message)
            return {'success': True, 'message': f"커밋 완료: {message}"}
        else:
            return {'success': False, 'error': '커밋할 변경사항이 없습니다'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@track_operation('git', 'branch')
def git_branch(branch_name: Optional[str] = None, create: bool = True) -> Dict[str, Any]:
    """브랜치 생성 또는 전환
    
    Args:
        branch_name: 브랜치 이름 (None이면 현재 브랜치 반환)
        create: 브랜치가 없을 때 생성할지 여부
    
    Returns:
        dict: 결과 정보
    """
    try:
        from git import Repo
        repo = Repo('.')
        
        if branch_name is None:
            # 현재 브랜치 반환
            return {'success': True, 'branch': repo.active_branch.name}
        
        # 브랜치 존재 확인
        if branch_name in [b.name for b in repo.branches]:
            repo.git.checkout(branch_name)
            return {'success': True, 'message': f"브랜치 전환: {branch_name}"}
        elif create:
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            return {'success': True, 'message': f"새 브랜치 생성 및 전환: {branch_name}"}
        else:
            return {'success': False, 'error': f"브랜치가 존재하지 않습니다: {branch_name}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@track_operation('git', 'stash')
def git_stash(message: Optional[str] = None) -> Dict[str, Any]:
    """현재 변경사항을 임시 저장
    
    Args:
        message: stash 메시지
    
    Returns:
        dict: 결과 정보
    """
    try:
        from git import Repo
        repo = Repo('.')
        
        if repo.is_dirty():
            if message:
                repo.git.stash('save', message)
            else:
                repo.git.stash()
            return {'success': True, 'message': 'Stash 저장 완료'}
        else:
            return {'success': False, 'error': '저장할 변경사항이 없습니다'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@track_operation('git', 'stash_pop')
def git_stash_pop() -> Dict[str, Any]:
    """임시 저장한 변경사항 복원
    
    Returns:
        dict: 결과 정보
    """
    try:
        from git import Repo
        repo = Repo('.')
        
        repo.git.stash('pop')
        return {'success': True, 'message': 'Stash 복원 완료'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@track_operation('git', 'log')
def git_log(n: int = 10) -> Dict[str, Any]:
    """최근 커밋 히스토리 조회
    
    Args:
        n: 조회할 커밋 개수
    
    Returns:
        dict: 커밋 목록
    """
    try:
        from git import Repo
        repo = Repo('.')
        
        commits = []
        for commit in repo.iter_commits(max_count=n):
            commits.append({
                'hash': commit.hexsha[:7],
                'author': str(commit.author),
                'date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M'),
                'message': commit.message.strip()
            })
        
        return {'success': True, 'commits': commits}
    except Exception as e:
        return {'success': False, 'error': str(e)}
