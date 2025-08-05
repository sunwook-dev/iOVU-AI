#!/usr/bin/env python3
"""
데이터 정리 유틸리티
- 데이터베이스의 모든 테이블 데이터 삭제 (구조 유지)
- data 디렉토리 내용 정리
- 로그 파일 정리
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.utils.connection import get_db
from database.config import Tables

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_cleanup.log')
    ]
)
logger = logging.getLogger(__name__)

class DataCleaner:
    """데이터 정리 클래스"""
    
    def __init__(self):
        self.db = get_db()
        self.project_root = project_root
        
    def get_all_tables(self) -> List[str]:
        """데이터베이스의 모든 테이블 목록 조회"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        
        try:
            results = self.db.execute(query, (self.db.config.database,))
            tables = [row['table_name'] for row in results]
            logger.info(f"Found {len(tables)} tables in database")
            return tables
        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []
    
    def get_table_row_count(self, table_name: str) -> int:
        """테이블의 행 개수 조회"""
        try:
            query = f"SELECT COUNT(*) as count FROM `{table_name}`"
            result = self.db.execute_one(query)
            return result['count'] if result else 0
        except Exception as e:
            logger.warning(f"Failed to count rows in {table_name}: {e}")
            return 0
    
    def disable_foreign_key_checks(self):
        """외래키 제약 조건 비활성화"""
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            logger.info("Foreign key checks disabled")
        except Exception as e:
            logger.error(f"Failed to disable foreign key checks: {e}")
    
    def enable_foreign_key_checks(self):
        """외래키 제약 조건 활성화"""
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            logger.info("Foreign key checks enabled")
        except Exception as e:
            logger.error(f"Failed to enable foreign key checks: {e}")
    
    def clean_database_tables(self) -> Dict[str, Any]:
        """모든 테이블 데이터 삭제"""
        logger.info("Starting database cleanup...")
        
        tables = self.get_all_tables()
        if not tables:
            logger.warning("No tables found in database")
            return {"success": False, "message": "No tables found"}
        
        # 삭제 전 상태 확인
        table_stats = {}
        for table in tables:
            count = self.get_table_row_count(table)
            table_stats[table] = {"before": count, "after": 0}
        
        total_rows_before = sum(stats["before"] for stats in table_stats.values())
        logger.info(f"Total rows before cleanup: {total_rows_before}")
        
        # 외래키 제약 조건 비활성화
        self.disable_foreign_key_checks()
        
        deleted_tables = []
        failed_tables = []
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                
                for table in tables:
                    try:
                        # TRUNCATE는 빠르지만 외래키가 있으면 실패할 수 있음
                        # DELETE는 느리지만 안전함
                        cursor.execute(f"TRUNCATE TABLE `{table}`")
                        deleted_tables.append(table)
                        logger.info(f"✅ Cleaned table: {table} ({table_stats[table]['before']} rows)")
                        
                    except Exception as e:
                        logger.warning(f"TRUNCATE failed for {table}, trying DELETE: {e}")
                        try:
                            cursor.execute(f"DELETE FROM `{table}`")
                            deleted_tables.append(table)
                            logger.info(f"✅ Cleaned table: {table} ({table_stats[table]['before']} rows)")
                        except Exception as delete_error:
                            failed_tables.append(table)
                            logger.error(f"❌ Failed to clean table {table}: {delete_error}")
        
        finally:
            # 외래키 제약 조건 재활성화
            self.enable_foreign_key_checks()
        
        # 삭제 후 상태 확인
        for table in deleted_tables:
            table_stats[table]["after"] = self.get_table_row_count(table)
        
        total_rows_after = sum(self.get_table_row_count(table) for table in tables)
        
        result = {
            "success": len(failed_tables) == 0,
            "total_tables": len(tables),
            "cleaned_tables": len(deleted_tables),
            "failed_tables": len(failed_tables),
            "failed_table_names": failed_tables,
            "rows_deleted": total_rows_before - total_rows_after,
            "table_stats": table_stats
        }
        
        if result["success"]:
            logger.info(f"✅ Database cleanup completed successfully!")
            logger.info(f"   - Tables cleaned: {len(deleted_tables)}")
            logger.info(f"   - Rows deleted: {total_rows_before - total_rows_after}")
        else:
            logger.error(f"❌ Database cleanup completed with errors!")
            logger.error(f"   - Failed tables: {failed_tables}")
        
        return result
    
    def clean_data_directory(self) -> Dict[str, Any]:
        """data 디렉토리 내용 정리"""
        logger.info("Starting data directory cleanup...")
        
        data_dir = self.project_root / "data"
        if not data_dir.exists():
            logger.info("Data directory does not exist")
            return {"success": True, "message": "Data directory does not exist"}
        
        # 삭제할 항목들 수집
        items_to_delete = []
        total_size = 0
        
        for item in data_dir.iterdir():
            if item.is_file():
                items_to_delete.append(item)
                total_size += item.stat().st_size
            elif item.is_dir():
                # 디렉토리 크기 계산
                for subitem in item.rglob("*"):
                    if subitem.is_file():
                        total_size += subitem.stat().st_size
                items_to_delete.append(item)
        
        logger.info(f"Found {len(items_to_delete)} items to delete ({total_size / 1024 / 1024:.2f} MB)")
        
        deleted_count = 0
        failed_items = []
        
        for item in items_to_delete:
            try:
                if item.is_file():
                    item.unlink()
                    logger.debug(f"Deleted file: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    logger.debug(f"Deleted directory: {item.name}")
                deleted_count += 1
            except Exception as e:
                failed_items.append(str(item))
                logger.error(f"Failed to delete {item}: {e}")
        
        result = {
            "success": len(failed_items) == 0,
            "total_items": len(items_to_delete),
            "deleted_items": deleted_count,
            "failed_items": len(failed_items),
            "failed_item_names": failed_items,
            "size_freed_mb": total_size / 1024 / 1024
        }
        
        if result["success"]:
            logger.info(f"✅ Data directory cleanup completed successfully!")
            logger.info(f"   - Items deleted: {deleted_count}")
            logger.info(f"   - Space freed: {total_size / 1024 / 1024:.2f} MB")
        else:
            logger.error(f"❌ Data directory cleanup completed with errors!")
            logger.error(f"   - Failed items: {failed_items}")
        
        return result
    
    def clean_log_files(self) -> Dict[str, Any]:
        """로그 파일 정리"""
        logger.info("Starting log files cleanup...")
        
        log_files = []
        
        # 프로젝트 루트의 logs 디렉토리
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            log_files.extend(logs_dir.glob("*.log"))
            log_files.extend(logs_dir.glob("*.jsonl"))
        
        # 각 에이전트의 logs 디렉토리
        for agent_dir in self.project_root.glob("agent_*/"):
            agent_logs = agent_dir / "logs"
            if agent_logs.exists():
                log_files.extend(agent_logs.glob("*.log"))
                log_files.extend(agent_logs.glob("*.jsonl"))
        
        # 출력 디렉토리들
        for agent_dir in self.project_root.glob("agent_*/"):
            outputs_dir = agent_dir / "outputs"
            if outputs_dir.exists():
                log_files.extend(outputs_dir.rglob("*"))
        
        total_size = sum(f.stat().st_size for f in log_files if f.is_file())
        logger.info(f"Found {len(log_files)} log files ({total_size / 1024 / 1024:.2f} MB)")
        
        deleted_count = 0
        failed_files = []
        
        for log_file in log_files:
            try:
                if log_file.is_file():
                    log_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted log file: {log_file}")
            except Exception as e:
                failed_files.append(str(log_file))
                logger.error(f"Failed to delete {log_file}: {e}")
        
        result = {
            "success": len(failed_files) == 0,
            "total_files": len(log_files),
            "deleted_files": deleted_count,
            "failed_files": len(failed_files),
            "failed_file_names": failed_files,
            "size_freed_mb": total_size / 1024 / 1024
        }
        
        if result["success"]:
            logger.info(f"✅ Log files cleanup completed successfully!")
            logger.info(f"   - Files deleted: {deleted_count}")
            logger.info(f"   - Space freed: {total_size / 1024 / 1024:.2f} MB")
        else:
            logger.error(f"❌ Log files cleanup completed with errors!")
            logger.error(f"   - Failed files: {failed_files}")
        
        return result
    
    def full_cleanup(self) -> Dict[str, Any]:
        """전체 데이터 정리 실행"""
        logger.info("="*60)
        logger.info("STARTING FULL DATA CLEANUP")
        logger.info("="*60)
        
        results = {
            "database": None,
            "data_directory": None,
            "log_files": None,
            "overall_success": False
        }
        
        try:
            # 1. 데이터베이스 정리
            results["database"] = self.clean_database_tables()
            
            # 2. 데이터 디렉토리 정리
            results["data_directory"] = self.clean_data_directory()
            
            # 3. 로그 파일 정리
            results["log_files"] = self.clean_log_files()
            
            # 전체 성공 여부 판단
            results["overall_success"] = all([
                results["database"]["success"],
                results["data_directory"]["success"],
                results["log_files"]["success"]
            ])
            
        except Exception as e:
            logger.error(f"Full cleanup failed: {e}")
            results["error"] = str(e)
        
        logger.info("="*60)
        if results["overall_success"]:
            logger.info("✅ FULL DATA CLEANUP COMPLETED SUCCESSFULLY!")
        else:
            logger.info("❌ FULL DATA CLEANUP COMPLETED WITH ERRORS!")
        logger.info("="*60)
        
        return results

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Cleanup Utility")
    parser.add_argument("--database-only", action="store_true", help="Clean database only")
    parser.add_argument("--data-only", action="store_true", help="Clean data directory only")
    parser.add_argument("--logs-only", action="store_true", help="Clean log files only")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    cleaner = DataCleaner()
    
    # 확인 프롬프트
    if not args.confirm:
        print("\n⚠️  WARNING: This will permanently delete all data!")
        print("   - Database: All table data (structure preserved)")
        print("   - Files: All content in data/ directory")
        print("   - Logs: All log files from agents")
        
        response = input("\nDo you want to proceed? (yes/no): ").lower().strip()
        if response != "yes":
            print("Cleanup cancelled.")
            return
    
    # 선택적 정리 실행
    if args.database_only:
        result = cleaner.clean_database_tables()
    elif args.data_only:
        result = cleaner.clean_data_directory()
    elif args.logs_only:
        result = cleaner.clean_log_files()
    else:
        # 전체 정리
        result = cleaner.full_cleanup()
    
    # 결과 출력
    print("\n" + "="*60)
    print("CLEANUP SUMMARY")
    print("="*60)
    
    if isinstance(result, dict) and "database" in result:
        # 전체 정리 결과
        for category, data in result.items():
            if category in ["database", "data_directory", "log_files"] and data:
                print(f"\n{category.replace('_', ' ').title()}:")
                print(f"  Success: {'✅' if data['success'] else '❌'}")
                if "rows_deleted" in data:
                    print(f"  Rows deleted: {data['rows_deleted']}")
                if "deleted_items" in data:
                    print(f"  Items deleted: {data['deleted_items']}")
                if "deleted_files" in data:
                    print(f"  Files deleted: {data['deleted_files']}")
                if "size_freed_mb" in data:
                    print(f"  Space freed: {data['size_freed_mb']:.2f} MB")
    else:
        # 개별 정리 결과
        print(f"Success: {'✅' if result['success'] else '❌'}")
        for key, value in result.items():
            if key != "success":
                print(f"  {key}: {value}")

if __name__ == "__main__":
    main()