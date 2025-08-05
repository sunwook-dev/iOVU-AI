#!/usr/bin/env python3
"""
파이프라인 대시보드 실행 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """대시보드 실행"""
    # 프로젝트 루트 디렉토리로 이동
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 환경 확인
    print("🔍 환경 확인 중...")
    
    # Python 버전 확인
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        return
    
    print(f"✅ Python {sys.version}")
    
    # 필요한 패키지 설치 확인
    try:
        import streamlit
        import plotly
        import psutil
        print("✅ 필요한 패키지가 설치되어 있습니다.")
    except ImportError as e:
        print(f"❌ 필요한 패키지가 누락되었습니다: {e}")
        print("다음 명령어로 설치하세요:")
        print("pip install -r requirements_pipeline.txt")
        return
    
    # 환경 변수 파일 확인
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  .env 파일이 없습니다. 필요에 따라 생성하세요.")
        print("예시:")
        print("DB_HOST=localhost")
        print("DB_USER=root")
        print("DB_PASSWORD=your_password")
        print("DB_NAME=modular_agents_db")
        print("OPENAI_API_KEY=your_openai_api_key")
        print("")
    
    # Streamlit 실행
    print("🚀 파이프라인 대시보드를 시작합니다...")
    print("브라우저에서 http://localhost:8501 로 접속하세요.")
    print("종료하려면 Ctrl+C를 누르세요.")
    print("")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "pipeline_dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 대시보드가 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 대시보드 실행 실패: {e}")
    except FileNotFoundError:
        print("❌ Streamlit이 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요: pip install streamlit")

if __name__ == "__main__":
    main()