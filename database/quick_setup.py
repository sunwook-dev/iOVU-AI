#!/usr/bin/env python3
"""
Quick Database Setup Script for Modular Agents
간단하게 데이터베이스를 설정하는 스크립트
"""

import os
import sys
import pymysql
from getpass import getpass
import argparse
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """프로그램 헤더 출력"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print("🚀 Modular Agents Database Quick Setup")
    print(f"{'='*60}{Colors.ENDC}\n")


def print_success(message):
    """성공 메시지 출력"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message):
    """에러 메시지 출력"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_info(message):
    """정보 메시지 출력"""
    print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")


def print_warning(message):
    """경고 메시지 출력"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def get_db_config():
    """데이터베이스 연결 정보 입력받기"""
    print(f"{Colors.OKCYAN}데이터베이스 연결 정보를 입력하세요:{Colors.ENDC}\n")
    
    # 기본값 제공
    host = input("Host [localhost]: ").strip() or "localhost"
    port = input("Port [3306]: ").strip() or "3306"
    user = input("User [root]: ").strip() or "root"
    password = getpass("Password: ")
    
    return {
        'host': host,
        'port': int(port),
        'user': user,
        'password': password
    }


def test_connection(config):
    """데이터베이스 연결 테스트"""
    try:
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        conn.close()
        return True
    except Exception as e:
        print_error(f"연결 실패: {e}")
        return False


def create_database(config):
    """데이터베이스 생성"""
    try:
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        
        # 데이터베이스 존재 확인
        cursor.execute("SHOW DATABASES LIKE 'modular_agents_db'")
        exists = cursor.fetchone() is not None
        
        if exists:
            print_warning("데이터베이스 'modular_agents_db'가 이미 존재합니다.")
            response = input("\n기존 데이터베이스를 삭제하고 새로 생성하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print_info("기존 데이터베이스를 유지합니다.")
                conn.close()
                return True
            
            # 기존 데이터베이스 삭제
            cursor.execute("DROP DATABASE modular_agents_db")
            print_success("기존 데이터베이스를 삭제했습니다.")
        
        # 데이터베이스 생성
        cursor.execute("""
            CREATE DATABASE modular_agents_db 
            CHARACTER SET utf8mb4 
            COLLATE utf8mb4_unicode_ci
        """)
        print_success("데이터베이스 'modular_agents_db'를 생성했습니다.")
        
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"데이터베이스 생성 실패: {e}")
        return False


def execute_sql_file(config, sql_file):
    """SQL 파일 실행"""
    try:
        # SQL 파일 읽기
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 연결
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database='modular_agents_db',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # SQL 문을 세미콜론으로 분리하여 실행
        sql_statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        total = len(sql_statements)
        
        print(f"\n{Colors.OKBLUE}SQL 문 실행 중...{Colors.ENDC}")
        
        for i, statement in enumerate(sql_statements, 1):
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    # 진행률 표시
                    progress = int((i / total) * 50)
                    print(f"\r[{'='*progress}{' '*(50-progress)}] {i}/{total}", end='', flush=True)
                except Exception as e:
                    if "already exists" in str(e):
                        continue  # 이미 존재하는 경우 무시
                    else:
                        print(f"\n{Colors.WARNING}경고: {e}{Colors.ENDC}")
        
        print()  # 새 줄
        conn.commit()
        conn.close()
        
        print_success("모든 테이블과 뷰가 생성되었습니다.")
        return True
        
    except Exception as e:
        print_error(f"SQL 파일 실행 실패: {e}")
        return False


def create_env_file(config):
    """환경 변수 파일 생성"""
    env_content = f"""# Database Configuration
DB_HOST={config['host']}
DB_PORT={config['port']}
DB_USER={config['user']}
DB_PASSWORD={config['password']}
DB_NAME=modular_agents_db

# API Keys (필요시 추가)
OPENAI_API_KEY=your-api-key-here

# Crawler Settings
WEB_CRAWLER_MAX_DEPTH=10
WEB_CRAWLER_MAX_PAGES=2000
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
"""
    
    env_path = Path(__file__).parent.parent / '.env'
    
    if env_path.exists():
        print_warning(".env 파일이 이미 존재합니다.")
        response = input("덮어쓰시겠습니까? (y/N): ")
        if response.lower() != 'y':
            return
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print_success(f".env 파일이 생성되었습니다: {env_path}")


def show_summary(config):
    """설정 요약 표시"""
    print(f"\n{Colors.HEADER}{'='*60}")
    print("📊 데이터베이스 설정 완료!")
    print(f"{'='*60}{Colors.ENDC}\n")
    
    print("연결 정보:")
    print(f"  - Host: {config['host']}")
    print(f"  - Port: {config['port']}")
    print(f"  - User: {config['user']}")
    print(f"  - Database: modular_agents_db")
    
    print("\n생성된 주요 테이블:")
    print("  - 01_brands (브랜드 정보)")
    print("  - products (제품 정보)")
    print("  - raw_web_data (웹 크롤링 데이터)")
    print("  - 03_raw_instagram_data (인스타그램 데이터)")
    print("  - cleaned_web_text (정제된 텍스트)")
    print("  - refined_content (정제된 콘텐츠)")
    print("  - extracted_keywords (추출된 키워드)")
    
    print(f"\n{Colors.OKGREEN}✨ 이제 modular agents를 사용할 준비가 되었습니다!{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description='Modular Agents 데이터베이스 빠른 설정')
    parser.add_argument('--host', help='MySQL 호스트')
    parser.add_argument('--port', type=int, help='MySQL 포트')
    parser.add_argument('--user', help='MySQL 사용자')
    parser.add_argument('--password', help='MySQL 비밀번호')
    parser.add_argument('--skip-env', action='store_true', help='.env 파일 생성 건너뛰기')
    
    args = parser.parse_args()
    
    print_header()
    
    # 연결 정보 설정
    if args.host and args.user and args.password:
        config = {
            'host': args.host,
            'port': args.port or 3306,
            'user': args.user,
            'password': args.password
        }
        print_info("명령줄 인수로 연결 정보를 받았습니다.")
    else:
        config = get_db_config()
    
    # 연결 테스트
    print(f"\n{Colors.OKBLUE}데이터베이스 연결 테스트 중...{Colors.ENDC}")
    if not test_connection(config):
        print_error("데이터베이스에 연결할 수 없습니다. 연결 정보를 확인하세요.")
        sys.exit(1)
    
    print_success("데이터베이스 연결 성공!")
    
    # 데이터베이스 생성
    if not create_database(config):
        sys.exit(1)
    
    # SQL 파일 실행
    sql_file = Path(__file__).parent / 'setup_database.sql'
    if not sql_file.exists():
        print_error(f"SQL 파일을 찾을 수 없습니다: {sql_file}")
        sys.exit(1)
    
    if not execute_sql_file(config, sql_file):
        sys.exit(1)
    
    # 환경 파일 생성
    if not args.skip_env:
        create_env_file(config)
    
    # 요약 표시
    show_summary(config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}설정이 취소되었습니다.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        sys.exit(1)