#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git 초기 설정 도우미
AI Coding Brain MCP 프로젝트의 Git 설정을 쉽게 도와줍니다.
"""

import os
import subprocess
import json
from pathlib import Path
import getpass


def run_command(cmd):
    """명령 실행"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def setup_git_config():
    """Git 기본 설정"""
    print("\n🔧 Git 사용자 정보 설정")
    
    # 현재 설정 확인
    success, name_out, _ = run_command("git config user.name")
    success2, email_out, _ = run_command("git config user.email")
    
    current_name = name_out.strip() if success else ""
    current_email = email_out.strip() if success2 else ""
    
    if current_name:
        print(f"현재 이름: {current_name}")
        change = input("변경하시겠습니까? (y/N): ").lower() == 'y'
        if not change:
            name = current_name
        else:
            name = input("새 이름: ").strip()
    else:
        name = input("Git 사용자 이름: ").strip()
    
    if current_email:
        print(f"현재 이메일: {current_email}")
        change = input("변경하시겠습니까? (y/N): ").lower() == 'y'
        if not change:
            email = current_email
        else:
            email = input("새 이메일: ").strip()
    else:
        email = input("Git 이메일: ").strip()
    
    if name:
        run_command(f'git config user.name "{name}"')
    if email:
        run_command(f'git config user.email "{email}"')
    
    print("✅ Git 사용자 정보 설정 완료")


def setup_github_remote():
    """GitHub 원격 저장소 설정"""
    print("\n🌐 GitHub 원격 저장소 설정")
    
    # 현재 원격 저장소 확인
    success, remotes, _ = run_command("git remote -v")
    
    if success and "origin" in remotes:
        print("현재 원격 저장소:")
        print(remotes)
        change = input("\n변경하시겠습니까? (y/N): ").lower() == 'y'
        if not change:
            return
    
    print("\nGitHub 저장소 정보를 입력하세요:")
    username = input("GitHub 사용자명 [337zzang]: ").strip() or "337zzang"
    repo = input("저장소 이름 [ai-coding-brain-mcp]: ").strip() or "ai-coding-brain-mcp"
    
    # HTTPS vs SSH 선택
    print("\n연결 방식을 선택하세요:")
    print("1. HTTPS (Personal Access Token 필요)")
    print("2. SSH (SSH 키 설정 필요)")
    choice = input("선택 [1]: ").strip() or "1"
    
    if choice == "2":
        url = f"git@github.com:{username}/{repo}.git"
    else:
        url = f"https://github.com/{username}/{repo}.git"
    
    # 원격 저장소 설정
    if "origin" in remotes:
        success, _, err = run_command(f'git remote set-url origin {url}')
    else:
        success, _, err = run_command(f'git remote add origin {url}')
    
    if success:
        print(f"✅ 원격 저장소 설정 완료: {url}")
    else:
        print(f"❌ 설정 실패: {err}")


def setup_credential_helper():
    """인증 정보 관리 설정"""
    print("\n🔐 Git 인증 정보 관리 설정")
    
    # 현재 설정 확인
    success, helper, _ = run_command("git config credential.helper")
    
    if success and helper.strip():
        print(f"현재 Credential Helper: {helper.strip()}")
        print("✅ 이미 설정되어 있습니다.")
    else:
        print("Windows Credential Manager를 사용하도록 설정합니다...")
        run_command("git config --global credential.helper manager")
        print("✅ Credential Helper 설정 완료")
    
    print("\n💡 팁: 첫 push 시 GitHub 로그인 창이 뜹니다.")
    print("   - Username: GitHub 사용자명")
    print("   - Password: Personal Access Token (비밀번호 아님!)")


def create_env_file():
    """환경 변수 파일 생성"""
    print("\n📄 환경 변수 파일 생성 (.env)")
    
    env_path = Path(".env")
    gitignore_path = Path(".gitignore")
    
    # .gitignore 확인
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        if '.env' not in gitignore_content:
            with open(gitignore_path, 'a') as f:
                f.write("\n# Environment variables\n.env\n")
            print("✅ .gitignore에 .env 추가됨")
    
    if env_path.exists():
        print("⚠️  .env 파일이 이미 존재합니다.")
        overwrite = input("덮어쓰시겠습니까? (y/N): ").lower() == 'y'
        if not overwrite:
            return
    
    print("\nGitHub Personal Access Token이 있다면 입력하세요.")
    print("(없으면 Enter를 누르고 나중에 추가하세요)")
    token = getpass.getpass("GitHub Token: ").strip()
    
    env_content = f"""# GitHub 인증 정보 (절대 커밋하지 마세요!)
GITHUB_TOKEN={token}
GITHUB_USERNAME=

# Git 자동 백업 설정
AUTO_GIT_COMMIT=true
GIT_COMMIT_INTERVAL=5

# 디버그 모드
DEBUG_GIT=false
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ .env 파일 생성 완료")
    print("⚠️  주의: .env 파일은 절대 커밋하지 마세요!")


def test_connection():
    """연결 테스트"""
    print("\n🧪 Git 연결 테스트")
    
    # Git 상태 확인
    success, status, _ = run_command("git status")
    if not success:
        print("❌ Git 저장소가 초기화되지 않았습니다.")
        init = input("초기화하시겠습니까? (Y/n): ").lower() != 'n'
        if init:
            run_command("git init")
            print("✅ Git 저장소 초기화 완료")
    
    # 원격 저장소 확인
    success, remotes, _ = run_command("git remote -v")
    if success and remotes.strip():
        print("\n원격 저장소 연결 상태:")
        print(remotes)
        
        # 연결 테스트
        print("\n원격 저장소 연결을 테스트합니다...")
        success, _, err = run_command("git ls-remote --heads origin")
        
        if success:
            print("✅ 원격 저장소 연결 성공!")
        else:
            if "Authentication failed" in err:
                print("❌ 인증 실패: Personal Access Token이 필요합니다.")
                print("💡 GITHUB_SETUP.md를 참고하여 PAT를 생성하세요.")
            else:
                print(f"❌ 연결 실패: {err}")
    else:
        print("⚠️  원격 저장소가 설정되지 않았습니다.")


def main():
    """메인 실행"""
    print("🚀 AI Coding Brain MCP - Git 설정 도우미")
    print("=" * 50)
    
    while True:
        print("\n메뉴를 선택하세요:")
        print("1. Git 사용자 정보 설정")
        print("2. GitHub 원격 저장소 설정")
        print("3. 인증 정보 관리 설정")
        print("4. 환경 변수 파일 생성")
        print("5. 연결 테스트")
        print("6. 전체 설정 (1-5 모두)")
        print("0. 종료")
        
        choice = input("\n선택: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            setup_git_config()
        elif choice == "2":
            setup_github_remote()
        elif choice == "3":
            setup_credential_helper()
        elif choice == "4":
            create_env_file()
        elif choice == "5":
            test_connection()
        elif choice == "6":
            setup_git_config()
            setup_github_remote()
            setup_credential_helper()
            create_env_file()
            test_connection()
        else:
            print("❌ 잘못된 선택입니다.")
    
    print("\n✅ Git 설정 도우미를 종료합니다.")


if __name__ == "__main__":
    main()
