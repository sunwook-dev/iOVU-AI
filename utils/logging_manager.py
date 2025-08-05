"""
통합 로깅 시스템
- 각 에이전트의 로그를 중앙화
- 실시간 로그 스트리밍
- 로그 레벨별 필터링
- 에러 발생 시 알림
"""

import logging
import logging.handlers
import json
import time
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class LogLevel(Enum):
    """로그 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AgentStatus(Enum):
    """에이전트 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class LogEntry:
    """로그 엔트리 데이터 클래스"""
    timestamp: str
    level: str
    agent_id: str
    agent_name: str
    stage: str
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class AgentProgress:
    """에이전트 진행 상황"""
    agent_id: str
    agent_name: str
    status: AgentStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    progress_percent: float = 0.0
    current_stage: str = ""
    total_stages: int = 0
    completed_stages: int = 0
    processed_items: int = 0
    total_items: int = 0
    error_count: int = 0
    warning_count: int = 0

class PipelineLoggingManager:
    """파이프라인 통합 로깅 관리자"""
    
    def __init__(self, log_dir: Path = None, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.log_dir = log_dir or Path("logs/pipeline")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 로그 큐와 이벤트
        self.log_queue = queue.Queue()
        self.subscribers: List[Callable[[LogEntry], None]] = []
        self.agent_progress: Dict[str, AgentProgress] = {}
        
        # 로깅 설정
        self._setup_logging()
        
        # 백그라운드 로그 처리 스레드
        self.log_processor_thread = None
        self.stop_event = threading.Event()
        self.start_log_processing()
        
        # 통계
        self.session_stats = {
            "start_time": datetime.now().isoformat(),
            "total_logs": 0,
            "error_count": 0,
            "warning_count": 0,
            "agents_completed": 0,
            "agents_failed": 0
        }
    
    def _setup_logging(self):
        """로깅 시스템 설정"""
        # 세션별 로그 파일
        session_log_file = self.log_dir / f"pipeline_{self.session_id}.log"
        error_log_file = self.log_dir / f"pipeline_{self.session_id}_errors.log"
        
        # 메인 로거 설정
        self.logger = logging.getLogger(f"pipeline_{self.session_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # 파일 핸들러 (모든 로그)
        file_handler = logging.handlers.RotatingFileHandler(
            session_log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 에러 파일 핸들러 (에러만)
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file, maxBytes=5*1024*1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # 사용자 정의 핸들러 (큐로 전송)
        queue_handler = QueueLogHandler(self.log_queue, self.session_id)
        queue_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(queue_handler)
    
    def start_log_processing(self):
        """백그라운드 로그 처리 시작"""
        if self.log_processor_thread is None or not self.log_processor_thread.is_alive():
            self.stop_event.clear()
            self.log_processor_thread = threading.Thread(
                target=self._process_logs, daemon=True
            )
            self.log_processor_thread.start()
    
    def stop_log_processing(self):
        """백그라운드 로그 처리 중지"""
        self.stop_event.set()
        if self.log_processor_thread and self.log_processor_thread.is_alive():
            self.log_processor_thread.join(timeout=2)
    
    def _process_logs(self):
        """백그라운드에서 로그 처리"""
        while not self.stop_event.is_set():
            try:
                # 큐에서 로그 엔트리 가져오기 (타임아웃 설정)
                log_entry = self.log_queue.get(timeout=1)
                
                # 통계 업데이트
                self.session_stats["total_logs"] += 1
                if log_entry.level == "ERROR":
                    self.session_stats["error_count"] += 1
                elif log_entry.level == "WARNING":
                    self.session_stats["warning_count"] += 1
                
                # 구독자들에게 로그 전송
                for subscriber in self.subscribers:
                    try:
                        subscriber(log_entry)
                    except Exception as e:
                        # 구독자 오류는 로깅하지 않음 (무한 루프 방지)
                        pass
                
                # 에이전트 진행 상황 업데이트
                self._update_agent_progress(log_entry)
                
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                # 로그 처리 중 오류 발생
                pass
    
    def _update_agent_progress(self, log_entry: LogEntry):
        """로그 엔트리를 기반으로 에이전트 진행 상황 업데이트"""
        agent_id = log_entry.agent_id
        
        if agent_id not in self.agent_progress:
            self.agent_progress[agent_id] = AgentProgress(
                agent_id=agent_id,
                agent_name=log_entry.agent_name,
                status=AgentStatus.PENDING
            )
        
        progress = self.agent_progress[agent_id]
        
        # 상태 업데이트
        if "시작" in log_entry.message or "Starting" in log_entry.message:
            progress.status = AgentStatus.RUNNING
            progress.start_time = log_entry.timestamp
            progress.current_stage = log_entry.stage
        elif "완료" in log_entry.message or "Completed" in log_entry.message:
            progress.status = AgentStatus.COMPLETED
            progress.end_time = log_entry.timestamp
            progress.progress_percent = 100.0
            self.session_stats["agents_completed"] += 1
        elif "실패" in log_entry.message or "Failed" in log_entry.message or log_entry.level == "ERROR":
            if progress.status != AgentStatus.FAILED:  # 중복 카운트 방지
                progress.status = AgentStatus.FAILED
                progress.end_time = log_entry.timestamp
                self.session_stats["agents_failed"] += 1
        
        # 에러/경고 카운트
        if log_entry.level == "ERROR":
            progress.error_count += 1
        elif log_entry.level == "WARNING":
            progress.warning_count += 1
        
        # 데이터에서 진행 정보 추출
        if log_entry.data:
            if "progress_percent" in log_entry.data:
                progress.progress_percent = log_entry.data["progress_percent"]
            if "processed_items" in log_entry.data:
                progress.processed_items = log_entry.data["processed_items"]
            if "total_items" in log_entry.data:
                progress.total_items = log_entry.data["total_items"]
            if "stage" in log_entry.data:
                progress.current_stage = log_entry.data["stage"]
    
    def subscribe(self, callback: Callable[[LogEntry], None]):
        """로그 엔트리 구독"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[LogEntry], None]):
        """로그 엔트리 구독 해제"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_agent_logger(self, agent_id: str, agent_name: str) -> 'AgentLogger':
        """특정 에이전트용 로거 생성"""
        return AgentLogger(self, agent_id, agent_name)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 반환"""
        return {
            **self.session_stats,
            "session_id": self.session_id,
            "current_time": datetime.now().isoformat(),
            "agent_progress": {aid: asdict(progress) for aid, progress in self.agent_progress.items()}
        }
    
    def get_recent_logs(self, limit: int = 100, level_filter: Optional[str] = None) -> List[LogEntry]:
        """최근 로그 엔트리 반환"""
        # 실제 구현에서는 파일이나 데이터베이스에서 로그를 읽어올 수 있음
        # 여기서는 간단한 구현
        return []
    
    def export_logs(self, output_file: Path = None, format: str = "json") -> Path:
        """로그를 파일로 내보내기"""
        if output_file is None:
            output_file = self.log_dir / f"pipeline_{self.session_id}_export.{format}"
        
        if format == "json":
            export_data = {
                "session_info": self.get_session_stats(),
                "agent_progress": {aid: asdict(progress) for aid, progress in self.agent_progress.items()}
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_file

class QueueLogHandler(logging.Handler):
    """큐로 로그를 전송하는 핸들러"""
    
    def __init__(self, log_queue: queue.Queue, session_id: str):
        super().__init__()
        self.log_queue = log_queue
        self.session_id = session_id
    
    def emit(self, record):
        try:
            # 로그 레코드에서 에이전트 정보 추출
            agent_id = getattr(record, 'agent_id', 'unknown')
            agent_name = getattr(record, 'agent_name', 'Unknown Agent')
            stage = getattr(record, 'stage', 'unknown')
            data = getattr(record, 'data', None)
            error = getattr(record, 'error', None)
            
            log_entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created).isoformat(),
                level=record.levelname,
                agent_id=agent_id,
                agent_name=agent_name,
                stage=stage,
                message=record.getMessage(),
                data=data,
                error=error,
                session_id=self.session_id
            )
            
            self.log_queue.put(log_entry)
        except Exception:
            self.handleError(record)

class AgentLogger:
    """개별 에이전트용 로거"""
    
    def __init__(self, manager: PipelineLoggingManager, agent_id: str, agent_name: str):
        self.manager = manager
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.logger = manager.logger
    
    def _log(self, level: str, message: str, stage: str = "general", 
             data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """로그 기록"""
        # 로그 레코드에 에이전트 정보 추가
        extra = {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'stage': stage,
            'data': data,
            'error': error
        }
        
        if level == "DEBUG":
            self.logger.debug(message, extra=extra)
        elif level == "INFO":
            self.logger.info(message, extra=extra)
        elif level == "WARNING":
            self.logger.warning(message, extra=extra)
        elif level == "ERROR":
            self.logger.error(message, extra=extra)
        elif level == "CRITICAL":
            self.logger.critical(message, extra=extra)
    
    def debug(self, message: str, stage: str = "general", data: Optional[Dict[str, Any]] = None):
        self._log("DEBUG", message, stage, data)
    
    def info(self, message: str, stage: str = "general", data: Optional[Dict[str, Any]] = None):
        self._log("INFO", message, stage, data)
    
    def warning(self, message: str, stage: str = "general", data: Optional[Dict[str, Any]] = None):
        self._log("WARNING", message, stage, data)
    
    def error(self, message: str, stage: str = "general", 
              data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        self._log("ERROR", message, stage, data, error)
    
    def critical(self, message: str, stage: str = "general", 
                 data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        self._log("CRITICAL", message, stage, data, error)
    
    def log_progress(self, stage: str, progress_percent: float, 
                     processed_items: int = 0, total_items: int = 0, message: str = None):
        """진행 상황 로그"""
        if message is None:
            message = f"{stage} 진행 중: {progress_percent:.1f}%"
        
        data = {
            "progress_percent": progress_percent,
            "processed_items": processed_items,
            "total_items": total_items,
            "stage": stage
        }
        
        self.info(message, stage=stage, data=data)
    
    def log_start(self, stage: str = "start", message: str = None):
        """시작 로그"""
        if message is None:
            message = f"{self.agent_name} 시작"
        self.info(message, stage=stage)
    
    def log_complete(self, stage: str = "complete", message: str = None):
        """완료 로그"""
        if message is None:
            message = f"{self.agent_name} 완료"
        self.info(message, stage=stage)
    
    def log_error(self, stage: str, message: str, error: Exception = None):
        """에러 로그"""
        error_str = str(error) if error else None
        self.error(message, stage=stage, error=error_str)

# 전역 로깅 매니저 인스턴스
_global_logging_manager: Optional[PipelineLoggingManager] = None

def get_logging_manager(session_id: str = None) -> PipelineLoggingManager:
    """전역 로깅 매니저 인스턴스 반환"""
    global _global_logging_manager
    if _global_logging_manager is None:
        _global_logging_manager = PipelineLoggingManager(session_id=session_id)
    return _global_logging_manager

def create_agent_logger(agent_id: str, agent_name: str, session_id: str = None) -> AgentLogger:
    """에이전트 로거 생성"""
    manager = get_logging_manager(session_id)
    return manager.get_agent_logger(agent_id, agent_name)

# 컨텍스트 매니저
class LoggingSession:
    """로깅 세션 컨텍스트 매니저"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.manager = None
    
    def __enter__(self) -> PipelineLoggingManager:
        self.manager = PipelineLoggingManager(session_id=self.session_id)
        return self.manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.manager:
            self.manager.stop_log_processing()

# 사용 예시
if __name__ == "__main__":
    # 로깅 세션 시작
    with LoggingSession("test_session") as logging_manager:
        # 에이전트 로거 생성
        agent1_logger = logging_manager.get_agent_logger("agent_01", "Query Collector")
        agent2_logger = logging_manager.get_agent_logger("agent_02", "Web Crawler")
        
        # 로그 구독자 설정
        def log_subscriber(log_entry: LogEntry):
            print(f"[{log_entry.timestamp}] {log_entry.agent_name}: {log_entry.message}")
        
        logging_manager.subscribe(log_subscriber)
        
        # 테스트 로그
        agent1_logger.log_start()
        agent1_logger.log_progress("collection", 50.0, 5, 10)
        agent1_logger.log_complete()
        
        agent2_logger.log_start()
        agent2_logger.log_error("crawling", "Connection failed", Exception("Network error"))
        
        # 통계 출력
        import time
        time.sleep(1)  # 로그 처리 대기
        stats = logging_manager.get_session_stats()
        print(f"\nSession Stats: {json.dumps(stats, indent=2)}")