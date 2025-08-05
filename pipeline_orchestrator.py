"""
파이프라인 오케스트레이터
- 전체 15개 에이전트의 순차 실행 관리
- 에이전트 간 데이터 의존성 검증
- 실시간 진행 상황 추적
- 오류 처리 및 복구
"""

import os
import sys
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logging_manager import PipelineLoggingManager, AgentStatus, LoggingSession
from utils.agent_manager import (
    AgentConfig, AgentRunner, AgentDependencyManager, 
    ExecutionResult, get_default_agent_configs
)
from database.utils.connection import get_db

class PipelineStatus(Enum):
    """파이프라인 상태"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    brand_id: int
    brand_name: str = ""
    target_agents: Optional[List[str]] = None  # 실행할 에이전트 ID 목록 (None이면 모두)
    skip_agents: Optional[List[str]] = None    # 건너뛸 에이전트 ID 목록
    stop_on_error: bool = True                 # 에러 시 중단 여부
    auto_retry: bool = True                    # 자동 재시도 여부
    max_parallel_agents: int = 3               # 최대 병렬 실행 에이전트 수
    validate_data: bool = True                 # 데이터 검증 여부
    cleanup_on_failure: bool = False           # 실패 시 데이터 정리 여부
    environment_vars: Dict[str, str] = None    # 추가 환경 변수

@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    session_id: str
    brand_id: int
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_agents: int = 0
    completed_agents: int = 0
    failed_agents: int = 0
    skipped_agents: int = 0
    agent_results: Dict[str, ExecutionResult] = None
    error_message: str = ""
    total_execution_time_seconds: float = 0.0

class DataValidator:
    """데이터 검증기"""
    
    def __init__(self):
        self.db = get_db()
    
    def validate_input_data(self, agent_config: AgentConfig, brand_id: int) -> Dict[str, Any]:
        """에이전트 입력 데이터 검증"""
        validation_result = {
            "valid": True,
            "missing_data": [],
            "data_counts": {},
            "warnings": []
        }
        
        if not agent_config.required_inputs:
            return validation_result
        
        try:
            for required_input in agent_config.required_inputs:
                # 테이블.컬럼 형식 파싱
                if '.' in required_input:
                    table_name, column_name = required_input.split('.', 1)
                else:
                    table_name = required_input
                    column_name = None
                
                # 테이블 존재 확인
                if not self.db.table_exists(table_name):
                    validation_result["valid"] = False
                    validation_result["missing_data"].append(f"Table '{table_name}' does not exist")
                    continue
                
                # 데이터 개수 확인
                # brands 테이블은 id 컬럼 사용, 다른 테이블은 brand_id 사용
                id_column = "id" if table_name == "brands" else "brand_id"
                
                if column_name:
                    # 특정 컬럼에 데이터가 있는지 확인
                    query = f"""
                    SELECT COUNT(*) as count 
                    FROM `{table_name}` 
                    WHERE `{id_column}` = %s AND `{column_name}` IS NOT NULL AND `{column_name}` != ''
                    """
                else:
                    # 전체 데이터 개수 확인
                    query = f"""
                    SELECT COUNT(*) as count 
                    FROM `{table_name}` 
                    WHERE `{id_column}` = %s
                    """
                
                result = self.db.execute_one(query, (brand_id,))
                count = result['count'] if result else 0
                validation_result["data_counts"][required_input] = count
                
                if count == 0:
                    validation_result["valid"] = False
                    validation_result["missing_data"].append(f"No data in '{required_input}' for brand_id {brand_id}")
                elif count < 5:  # 경고: 데이터가 너무 적음
                    validation_result["warnings"].append(f"Low data count in '{required_input}': {count} records")
        
        except Exception as e:
            validation_result["valid"] = False
            validation_result["missing_data"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def validate_output_data(self, agent_config: AgentConfig, brand_id: int) -> Dict[str, Any]:
        """에이전트 출력 데이터 검증"""
        validation_result = {
            "valid": True,
            "data_counts": {},
            "warnings": []
        }
        
        if not agent_config.output_tables:
            return validation_result
        
        try:
            for table_name in agent_config.output_tables:
                if not self.db.table_exists(table_name):
                    validation_result["warnings"].append(f"Output table '{table_name}' does not exist")
                    continue
                
                # brands 테이블은 id 컬럼 사용, 다른 테이블은 brand_id 사용
                id_column = "id" if table_name == "brands" else "brand_id"
                
                query = f"""
                SELECT COUNT(*) as count 
                FROM `{table_name}` 
                WHERE `{id_column}` = %s
                """
                
                result = self.db.execute_one(query, (brand_id,))
                count = result['count'] if result else 0
                validation_result["data_counts"][table_name] = count
                
                if count == 0:
                    validation_result["warnings"].append(f"No output data in '{table_name}' for brand_id {brand_id}")
        
        except Exception as e:
            validation_result["valid"] = False
            validation_result["warnings"].append(f"Output validation error: {str(e)}")
        
        return validation_result

class PipelineOrchestrator:
    """파이프라인 오케스트레이터"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.logging_manager = PipelineLoggingManager(session_id=session_id)
        self.logger = self.logging_manager.get_agent_logger("orchestrator", "Pipeline Orchestrator")
        
        # 에이전트 설정
        self.agent_configs = get_default_agent_configs()
        self.dependency_manager = AgentDependencyManager(self.agent_configs)
        self.data_validator = DataValidator()
        
        # 실행 상태
        self.status = PipelineStatus.PENDING
        self.current_config: Optional[PipelineConfig] = None
        self.execution_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # 결과
        self.pipeline_result: Optional[PipelineResult] = None
        self.agent_runners: Dict[str, AgentRunner] = {}
        
        # 콜백
        self.status_callbacks: List[Callable[[PipelineStatus], None]] = []
        self.progress_callbacks: List[Callable[[str, float], None]] = []
    
    def add_status_callback(self, callback: Callable[[PipelineStatus], None]):
        """상태 변경 콜백 추가"""
        self.status_callbacks.append(callback)
    
    def add_progress_callback(self, callback: Callable[[str, float], None]):
        """진행률 콜백 추가 (agent_id, progress_percent)"""
        self.progress_callbacks.append(callback)
    
    def _notify_status_change(self, new_status: PipelineStatus):
        """상태 변경 알림"""
        self.status = new_status
        for callback in self.status_callbacks:
            try:
                callback(new_status)
            except Exception as e:
                self.logger.warning(f"Status callback error: {str(e)}")
    
    def _notify_progress(self, agent_id: str, progress_percent: float):
        """진행률 알림"""
        for callback in self.progress_callbacks:
            try:
                callback(agent_id, progress_percent)
            except Exception as e:
                self.logger.warning(f"Progress callback error: {str(e)}")
    
    def execute_pipeline(self, config: PipelineConfig) -> PipelineResult:
        """파이프라인 실행"""
        if self.status == PipelineStatus.RUNNING:
            raise RuntimeError("Pipeline is already running")
        
        self.current_config = config
        self.stop_event.clear()
        self.pause_event.clear()
        
        # 결과 초기화
        self.pipeline_result = PipelineResult(
            session_id=self.session_id,
            brand_id=config.brand_id,
            status=PipelineStatus.PENDING,
            start_time=datetime.now(),
            agent_results={}
        )
        
        # 백그라운드에서 실행
        self.execution_thread = threading.Thread(target=self._execute_pipeline_thread, daemon=False)
        self.execution_thread.start()
        
        return self.pipeline_result
    
    def _execute_pipeline_thread(self):
        """파이프라인 실행 스레드"""
        try:
            self._notify_status_change(PipelineStatus.RUNNING)
            self.logger.log_start(message=f"파이프라인 실행 시작 (Brand ID: {self.current_config.brand_id})")
            
            # 실행할 에이전트 목록 결정
            execution_order = self._determine_execution_order()
            self.pipeline_result.total_agents = len(execution_order)
            
            self.logger.info(f"실행 순서: {', '.join(execution_order)}", stage="planning")
            
            # 에이전트 순차 실행
            completed_agents = set()
            
            for i, agent_id in enumerate(execution_order):
                if self.stop_event.is_set():
                    self._notify_status_change(PipelineStatus.CANCELLED)
                    return
                
                # 일시정지 확인
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    time.sleep(1)
                
                if self.stop_event.is_set():
                    self._notify_status_change(PipelineStatus.CANCELLED)
                    return
                
                agent_config = self._get_agent_config(agent_id)
                if not agent_config:
                    self.logger.error(f"에이전트 설정을 찾을 수 없습니다: {agent_id}")
                    continue
                
                self.logger.info(f"에이전트 실행 중 ({i+1}/{len(execution_order)}): {agent_config.agent_name}")
                
                # 데이터 검증
                if self.current_config.validate_data:
                    validation_result = self.data_validator.validate_input_data(agent_config, self.current_config.brand_id)
                    if not validation_result["valid"]:
                        self.logger.error(f"입력 데이터 검증 실패: {agent_id}", error=str(validation_result["missing_data"]))
                        if self.current_config.stop_on_error:
                            self.pipeline_result.status = PipelineStatus.FAILED
                            self.pipeline_result.error_message = f"Data validation failed for {agent_id}"
                            self._notify_status_change(PipelineStatus.FAILED)
                            return
                        else:
                            self.pipeline_result.skipped_agents += 1
                            continue
                
                # 에이전트 실행
                result = self._execute_agent(agent_config)
                self.pipeline_result.agent_results[agent_id] = result
                
                if result.success:
                    completed_agents.add(agent_id)
                    self.pipeline_result.completed_agents += 1
                    self.logger.info(f"에이전트 완료: {agent_config.agent_name}")
                    
                    # 출력 데이터 검증
                    if self.current_config.validate_data:
                        output_validation = self.data_validator.validate_output_data(agent_config, self.current_config.brand_id)
                        for warning in output_validation["warnings"]:
                            self.logger.warning(warning)
                else:
                    self.pipeline_result.failed_agents += 1
                    self.logger.error(f"에이전트 실패: {agent_config.agent_name}", error=result.error_message)
                    
                    if self.current_config.stop_on_error:
                        self.pipeline_result.status = PipelineStatus.FAILED
                        self.pipeline_result.error_message = f"Agent {agent_id} failed: {result.error_message}"
                        self._notify_status_change(PipelineStatus.FAILED)
                        return
                
                # 진행률 업데이트
                progress = ((i + 1) / len(execution_order)) * 100
                self._notify_progress("pipeline", progress)
            
            # 파이프라인 완료
            self.pipeline_result.end_time = datetime.now()
            self.pipeline_result.total_execution_time_seconds = (
                self.pipeline_result.end_time - self.pipeline_result.start_time
            ).total_seconds()
            
            if self.pipeline_result.failed_agents == 0:
                self.pipeline_result.status = PipelineStatus.COMPLETED
                self._notify_status_change(PipelineStatus.COMPLETED)
                self.logger.log_complete(message=f"파이프라인 완료 ({self.pipeline_result.total_execution_time_seconds:.1f}초)")
            else:
                self.pipeline_result.status = PipelineStatus.FAILED
                self._notify_status_change(PipelineStatus.FAILED)
                self.logger.error(f"파이프라인 부분 실패: {self.pipeline_result.failed_agents}개 에이전트 실패")
        
        except Exception as e:
            self.pipeline_result.status = PipelineStatus.FAILED
            self.pipeline_result.error_message = str(e)
            self._notify_status_change(PipelineStatus.FAILED)
            self.logger.error(f"파이프라인 실행 중 오류: {str(e)}", error=str(e))
    
    def _determine_execution_order(self) -> List[str]:
        """실행 순서 결정"""
        all_agents = self.dependency_manager.get_execution_order()
        
        # 타겟 에이전트 필터링
        if self.current_config.target_agents:
            # 타겟 에이전트와 그 의존성들만 포함
            target_set = set(self.current_config.target_agents)
            for agent_id in self.current_config.target_agents:
                target_set.update(self._get_all_dependencies(agent_id))
            execution_order = [aid for aid in all_agents if aid in target_set]
        else:
            execution_order = all_agents
        
        # 건너뛸 에이전트 제외
        if self.current_config.skip_agents:
            execution_order = [aid for aid in execution_order if aid not in self.current_config.skip_agents]
        
        return execution_order
    
    def _get_all_dependencies(self, agent_id: str) -> set:
        """에이전트의 모든 의존성 재귀적으로 가져오기"""
        dependencies = set()
        direct_deps = self.dependency_manager.get_dependencies(agent_id)
        
        for dep in direct_deps:
            dependencies.add(dep)
            dependencies.update(self._get_all_dependencies(dep))
        
        return dependencies
    
    def _get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """에이전트 설정 가져오기"""
        for config in self.agent_configs:
            if config.agent_id == agent_id:
                return config
        return None
    
    def _execute_agent(self, agent_config: AgentConfig) -> ExecutionResult:
        """개별 에이전트 실행"""
        # 에이전트 로거 생성
        agent_logger = self.logging_manager.get_agent_logger(agent_config.agent_id, agent_config.agent_name)
        
        # 에이전트 러너 생성
        runner = AgentRunner(agent_config, agent_logger)
        self.agent_runners[agent_config.agent_id] = runner
        
        # 실행 파라미터 준비
        execution_params = {
            "brand_id": self.current_config.brand_id
        }
        
        # 브랜드명이 있으면 추가
        if self.current_config.brand_name:
            execution_params["brand_name"] = self.current_config.brand_name
        
        # 에이전트별 특수 파라미터
        if agent_config.agent_id == "agent_15":  # Blog GEO Analyzer
            execution_params["platform"] = "naver"  # 기본값
            execution_params["posts_limit"] = 10
        
        # 환경 변수 설정
        if self.current_config.environment_vars:
            for key, value in self.current_config.environment_vars.items():
                os.environ[key] = value
        
        # 에이전트 실행
        return runner.execute(**execution_params)
    
    def pause_pipeline(self):
        """파이프라인 일시정지"""
        if self.status == PipelineStatus.RUNNING:
            self.pause_event.set()
            self._notify_status_change(PipelineStatus.PAUSED)
            self.logger.info("파이프라인 일시정지")
    
    def resume_pipeline(self):
        """파이프라인 재개"""
        if self.status == PipelineStatus.PAUSED:
            self.pause_event.clear()
            self._notify_status_change(PipelineStatus.RUNNING)
            self.logger.info("파이프라인 재개")
    
    def stop_pipeline(self):
        """파이프라인 중지"""
        self.stop_event.set()
        self.pause_event.clear()
        
        # 실행 중인 에이전트 종료
        for runner in self.agent_runners.values():
            # AgentRunner에 terminate 메서드가 있다면 호출
            pass
        
        self._notify_status_change(PipelineStatus.CANCELLED)
        self.logger.info("파이프라인 중지")
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        stats = self.logging_manager.get_session_stats()
        
        result = {
            "session_id": self.session_id,
            "status": self.status.value,
            "current_time": datetime.now().isoformat(),
            "logging_stats": stats
        }
        
        if self.pipeline_result:
            result["pipeline_result"] = asdict(self.pipeline_result)
        
        if self.current_config:
            result["config"] = asdict(self.current_config)
        
        return result
    
    def wait_for_completion(self, timeout_seconds: Optional[int] = None) -> PipelineResult:
        """파이프라인 완료 대기"""
        if self.execution_thread:
            self.execution_thread.join(timeout=timeout_seconds)
        
        return self.pipeline_result
    
    def export_results(self, output_file: Path = None) -> Path:
        """결과 내보내기"""
        if output_file is None:
            output_file = Path(f"pipeline_results_{self.session_id}.json")
        
        export_data = {
            "pipeline_result": asdict(self.pipeline_result) if self.pipeline_result else None,
            "config": asdict(self.current_config) if self.current_config else None,
            "logging_stats": self.logging_manager.get_session_stats(),
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return output_file

# 편의 함수들
def create_pipeline_orchestrator(session_id: str = None) -> PipelineOrchestrator:
    """파이프라인 오케스트레이터 생성"""
    return PipelineOrchestrator(session_id=session_id)

def run_full_pipeline(brand_id: int, brand_name: str = "", **kwargs) -> PipelineResult:
    """전체 파이프라인 실행 (동기)"""
    config = PipelineConfig(
        brand_id=brand_id,
        brand_name=brand_name,
        **kwargs
    )
    
    orchestrator = create_pipeline_orchestrator()
    result = orchestrator.execute_pipeline(config)
    return orchestrator.wait_for_completion()

if __name__ == "__main__":
    # 테스트 실행
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline Orchestrator")
    parser.add_argument("brand_id", type=int, help="Brand ID")
    parser.add_argument("--brand-name", help="Brand name")
    parser.add_argument("--target-agents", nargs="+", help="Target agent IDs")
    parser.add_argument("--skip-agents", nargs="+", help="Skip agent IDs")
    parser.add_argument("--no-stop-on-error", action="store_true", help="Continue on error")
    parser.add_argument("--export", help="Export results to file")
    
    args = parser.parse_args()
    
    # 설정 생성
    config = PipelineConfig(
        brand_id=args.brand_id,
        brand_name=args.brand_name or "",
        target_agents=args.target_agents,
        skip_agents=args.skip_agents,
        stop_on_error=not args.no_stop_on_error
    )
    
    # 파이프라인 실행
    orchestrator = create_pipeline_orchestrator()
    
    # 진행 상황 출력
    def status_callback(status: PipelineStatus):
        print(f"Status: {status.value}")
    
    def progress_callback(agent_id: str, progress: float):
        print(f"Progress: {agent_id} - {progress:.1f}%")
    
    orchestrator.add_status_callback(status_callback)
    orchestrator.add_progress_callback(progress_callback)
    
    # 실행 및 대기
    result = orchestrator.execute_pipeline(config)
    final_result = orchestrator.wait_for_completion()
    
    # 결과 출력
    print(f"\nPipeline completed: {final_result.status.value}")
    print(f"Total agents: {final_result.total_agents}")
    print(f"Completed: {final_result.completed_agents}")
    print(f"Failed: {final_result.failed_agents}")
    print(f"Execution time: {final_result.total_execution_time_seconds:.1f}s")
    
    # 결과 내보내기
    if args.export:
        export_file = orchestrator.export_results(Path(args.export))
        print(f"Results exported to: {export_file}")