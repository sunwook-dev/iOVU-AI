#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 실행 스크립트
"""
import pymysql
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 데이터베이스 연결 정보
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'modular_agents_db'),
    'charset': 'utf8mb4'
}

def run_migration(migration_file):
    """단일 마이그레이션 파일 실행"""
    print(f"\n🔄 마이그레이션 실행: {os.path.basename(migration_file)}")
    
    try:
        # SQL 파일 읽기
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 데이터베이스 연결
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # SQL 명령을 세미콜론으로 분리하여 실행
        sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        for sql_command in sql_commands:
            if sql_command and not sql_command.startswith('--'):
                print(f"   실행중: {sql_command[:50]}...")
                cursor.execute(sql_command)
        
        # 변경사항 커밋
        connection.commit()
        print(f"   ✅ 성공적으로 완료!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"   ❌ 오류 발생: {str(e)}")
        return False
    
    return True

def main():
    """메인 실행 함수"""
    print("=== 데이터베이스 마이그레이션 시작 ===")
    
    # 마이그레이션 파일 목록
    migrations = [
        "/Users/paek/Desktop/final2/modular_agents/database/migrations/03_rename_tistory_table_and_drop_columns.sql",
        "/Users/paek/Desktop/final2/modular_agents/database/migrations/04_drop_brand_domain_tree.sql"
    ]
    
    # 각 마이그레이션 실행
    for migration_file in migrations:
        if os.path.exists(migration_file):
            run_migration(migration_file)
        else:
            print(f"⚠️  파일을 찾을 수 없음: {migration_file}")
    
    # 현재 테이블 구조 확인
    print("\n=== 현재 테이블 구조 확인 ===")
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 05_raw_tistory_data 테이블 확인
        print("\n📋 05_raw_tistory_data 테이블:")
        cursor.execute("SHOW COLUMNS FROM `05_raw_tistory_data`")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")
        
        # 01_brands 테이블 확인
        print("\n📋 01_brands 테이블:")
        cursor.execute("SHOW COLUMNS FROM `01_brands`")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"테이블 구조 확인 중 오류: {str(e)}")
    
    print("\n=== 마이그레이션 완료 ===")

if __name__ == "__main__":
    main()