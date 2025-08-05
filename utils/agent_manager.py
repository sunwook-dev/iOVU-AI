"""
에이전트 실행 관리자
- 개별 에이전트 실행 및 모니터링
- 에이전트 간 의존성 관리
- 오류 처리 및 재시도 로직
- 리소스 관리
"""

import os
import sys
import subprocess
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import signal
import psutil
from datetime import datetime, timedelta

from .logging_manager import AgentLogger, AgentStatus

class ExecutionMode(Enum):
    """실행 모드"""
    SEQUENTIAL = "sequential"  # 순차 실행
    PARALLEL = "parallel"      # 병렬 실행
    CONDITIONAL = "conditional"  # 조건부 실행

@dataclass
class AgentConfig:
    """에이전트 설정"""
    agent_id: str
    agent_name: str
    agent_path: Path
    script_name: str = "main.py"
    dependencies: List[str] = None  # 의존하는 에이전트 ID 목록
    required_inputs: List[str] = None  # 필요한 입력 데이터
    output_tables: List[str] = None   # 생성하는 출력 테이블
    timeout_minutes: int = 30
    retry_count: int = 2
    retry_delay_seconds: int = 60
    memory_limit_mb: int = 2048
    cpu_limit_percent: int = 80
    environment_vars: Dict[str, str] = None
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL

@dataclass
class ExecutionResult:
    """실행 결과"""
    agent_id: str
    success: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""
    retry_count: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    execution_time_seconds: float = 0.0

class AgentProcess:
    """실행 중인 에이전트 프로세스"""
    
    def __init__(self, config: AgentConfig, logger: AgentLogger):
        self.config = config
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
        self.psutil_process: Optional[psutil.Process] = None
        self.start_time: Optional[datetime] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
    def start(self, **kwargs) -> bool:
        """에이전트 프로세스 시작"""
        try:
            self.logger.log_start(message=f"{self.config.agent_name} 실행 시작")
            
            # 작업 디렉토리 설정
            cwd = self.config.agent_path
            
            # 실행 명령어 구성
            cmd = [sys.executable, self.config.script_name]
            
            # 명령줄 인수 추가
            for key, value in kwargs.items():
                if key.startswith('--'):
                    cmd.append(key)
                    if value is not None:
                        cmd.append(str(value))
                else:
                    cmd.extend([f"--{key.replace('_', '-')}", str(value)])
            
            # 환경 변수 설정
            env = os.environ.copy()
            if self.config.environment_vars:
                env.update(self.config.environment_vars)
            
            self.logger.info(f"실행 명령어: {' '.join(cmd)}", stage="execution")
            self.logger.info(f"작업 디렉토리: {cwd}", stage="execution")
            
            # 프로세스 시작
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.start_time = datetime.now()
            
            # psutil 프로세스 래퍼
            try:
                self.psutil_process = psutil.Process(self.process.pid)
            except psutil.NoSuchProcess:
                self.logger.warning("psutil 프로세스 모니터링을 시작할 수 없습니다")
            
            # 모니터링 스레드 시작
            self.start_monitoring()
            
            self.logger.info(f"프로세스 시작됨 (PID: {self.process.pid})", stage="execution")
            return True
            
        except Exception as e:
            self.logger.error(f"프로세스 시작 실패: {str(e)}", stage="execution", error=str(e))
            return False
    
    def start_monitoring(self):
        """리소스 모니터링 시작"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.stop_monitoring.clear()
            self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
            self.monitor_thread.start()
    
    def _monitor_resources(self):
        """리소스 사용량 모니터링"""
        while not self.stop_monitoring.is_set():
            try:
                if self.psutil_process and self.psutil_process.is_running():
                    # CPU 및 메모리 사용량 확인
                    cpu_percent = self.psutil_process.cpu_percent()
                    memory_info = self.psutil_process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    
                    # 제한 확인
                    if memory_mb > self.config.memory_limit_mb:
                        self.logger.warning(
                            f"메모리 사용량 초과: {memory_mb:.1f}MB > {self.config.memory_limit_mb}MB",
                            stage="monitoring"
                        )
                    
                    if cpu_percent > self.config.cpu_limit_percent:
                        self.logger.warning(
                            f"CPU 사용량 초과: {cpu_percent:.1f}% > {self.config.cpu_limit_percent}%",
                            stage="monitoring"
                        )
                    
                    # 진행 상황 로그
                    self.logger.debug(
                        f"리소스 사용량 - CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB",
                        stage="monitoring",
                        data={"cpu_percent": cpu_percent, "memory_mb": memory_mb}
                    )
                
                time.sleep(10)  # 10초마다 모니터링
                
            except psutil.NoSuchProcess:
                break  # 프로세스가 종료됨
            except Exception as e:
                self.logger.debug(f"모니터링 오류: {str(e)}", stage="monitoring")
                time.sleep(10)
    
    def wait(self, timeout_seconds: Optional[int] = None) -> ExecutionResult:
        """프로세스 완료 대기"""
        if not self.process:
            return ExecutionResult(
                agent_id=self.config.agent_id,
                success=False,
                start_time=datetime.now(),
                error_message="프로세스가 시작되지 않음"
            )
        
        try:
            # 타임아웃 설정
            timeout = timeout_seconds or (self.config.timeout_minutes * 60)
            
            # 프로세스 완료 대기
            stdout, stderr = self.process.communicate(timeout=timeout)
            exit_code = self.process.returncode
            
            # 모니터링 중지
            self.stop_monitoring.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)
            
            end_time = datetime.now()
            execution_time = (end_time - self.start_time).total_seconds()
            
            # 최종 리소스 사용량
            memory_mb = 0.0
            cpu_percent = 0.0
            if self.psutil_process:
                try:
                    memory_info = self.psutil_process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    cpu_percent = self.psutil_process.cpu_percent()
                except:
                    pass
            
            success = exit_code == 0
            
            result = ExecutionResult(
                agent_id=self.config.agent_id,
                success=success,
                start_time=self.start_time,
                end_time=end_time,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                error_message="" if success else f"Exit code: {exit_code}",
                memory_usage_mb=memory_mb,
                cpu_usage_percent=cpu_percent,
                execution_time_seconds=execution_time
            )
            
            if success:
                self.logger.log_complete(
                    message=f"{self.config.agent_name} 실행 완료 ({execution_time:.1f}초)"
                )
            else:
                self.logger.error(
                    f"{self.config.agent_name} 실행 실패: exit code {exit_code}",
                    stage="execution",
                    error=stderr[:500] if stderr else "Unknown error"
                )
            
            return result
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"실행 시간 초과 ({timeout}초)", stage="execution")
            self.terminate()
            return ExecutionResult(
                agent_id=self.config.agent_id,
                success=False,
                start_time=self.start_time,
                end_time=datetime.now(),
                error_message=f"Timeout after {timeout} seconds"
            )
            
        except Exception as e:
            self.logger.error(f"실행 중 오류: {str(e)}", stage="execution", error=str(e))
            return ExecutionResult(
                agent_id=self.config.agent_id,
                success=False,
                start_time=self.start_time,
                end_time=datetime.now(),
                error_message=str(e)
            )
    
    def terminate(self):
        """프로세스 강제 종료"""
        if self.process:
            try:
                # 모니터링 중지
                self.stop_monitoring.set()
                
                # 프로세스 종료
                if self.psutil_process and self.psutil_process.is_running():
                    # 자식 프로세스들도 함께 종료
                    children = self.psutil_process.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass
                    
                    # 메인 프로세스 종료
                    self.psutil_process.terminate()
                    
                    # 강제 종료 대기
                    try:
                        self.psutil_process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        self.psutil_process.kill()
                        self.psutil_process.wait(timeout=5)
                
                else:
                    # psutil이 없는 경우 subprocess로 종료
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
                
                self.logger.info("프로세스 종료됨", stage="execution")
                
            except Exception as e:
                self.logger.error(f"프로세스 종료 실패: {str(e)}", stage="execution")

class AgentRunner:
    """개별 에이전트 실행기"""
    
    def __init__(self, config: AgentConfig, logger: AgentLogger):
        self.config = config
        self.logger = logger
        self.execution_history: List[ExecutionResult] = []
    
    def execute(self, **kwargs) -> ExecutionResult:
        """에이전트 실행 (재시도 포함)"""
        self.logger.info(f"{self.config.agent_name} 실행 시작", stage="start")
        
        for attempt in range(self.config.retry_count + 1):
            if attempt > 0:
                self.logger.info(f"재시도 {attempt}/{self.config.retry_count}", stage="retry")
                time.sleep(self.config.retry_delay_seconds)
            
            # 에이전트 프로세스 생성 및 실행
            process = AgentProcess(self.config, self.logger)
            
            if not process.start(**kwargs):
                continue
            
            # 실행 완료 대기
            result = process.wait()
            result.retry_count = attempt
            
            self.execution_history.append(result)
            
            if result.success:
                self.logger.info(f"{self.config.agent_name} 실행 성공", stage="complete")
                return result
            else:
                self.logger.error(
                    f"{self.config.agent_name} 실행 실패 (시도 {attempt + 1})",
                    stage="error",
                    error=result.error_message
                )
        
        # 모든 재시도 실패
        final_result = self.execution_history[-1] if self.execution_history else ExecutionResult(
            agent_id=self.config.agent_id,
            success=False,
            start_time=datetime.now(),
            error_message="실행 시작 실패"
        )
        
        self.logger.error(f"{self.config.agent_name} 최종 실패", stage="failed")
        return final_result
    
    def get_last_result(self) -> Optional[ExecutionResult]:
        """마지막 실행 결과 반환"""
        return self.execution_history[-1] if self.execution_history else None

class AgentDependencyManager:
    """에이전트 의존성 관리자"""
    
    def __init__(self, agents: List[AgentConfig]):
        self.agents = {agent.agent_id: agent for agent in agents}
        self.dependency_graph = self._build_dependency_graph()
        self.execution_order = self._calculate_execution_order()
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """의존성 그래프 구축"""
        graph = {}
        for agent in self.agents.values():
            graph[agent.agent_id] = agent.dependencies or []
        return graph
    
    def _calculate_execution_order(self) -> List[str]:
        """토폴로지 정렬을 통한 실행 순서 계산"""
        visited = set()
        temp_visited = set()
        order = []
        
        def dfs(agent_id: str):
            if agent_id in temp_visited:
                raise ValueError(f"순환 의존성 발견: {agent_id}")
            if agent_id in visited:
                return
            
            temp_visited.add(agent_id)
            
            for dependency in self.dependency_graph.get(agent_id, []):
                if dependency not in self.agents:
                    raise ValueError(f"존재하지 않는 의존성: {dependency}")
                dfs(dependency)
            
            temp_visited.remove(agent_id)
            visited.add(agent_id)
            order.append(agent_id)
        
        for agent_id in self.agents:
            if agent_id not in visited:
                dfs(agent_id)
        
        return order
    
    def get_execution_order(self) -> List[str]:
        """실행 순서 반환"""
        return self.execution_order.copy()
    
    def get_dependencies(self, agent_id: str) -> List[str]:
        """특정 에이전트의 의존성 반환"""
        return self.dependency_graph.get(agent_id, []).copy()
    
    def can_execute(self, agent_id: str, completed_agents: set) -> bool:
        """에이전트 실행 가능 여부 확인"""
        dependencies = self.get_dependencies(agent_id)
        return all(dep in completed_agents for dep in dependencies)

# 예시 에이전트 설정들
def get_default_agent_configs() -> List[AgentConfig]:
    """기본 에이전트 설정 목록"""
    project_root = Path(__file__).parent.parent
    
    configs = [
        AgentConfig(
            agent_id="agent_01",
            agent_name="Query Collector",
            agent_path=project_root / "agent_01_query_collector",
            script_name="cli.py",
            dependencies=[],
            output_tables=["brands", "brand_channels"],
            timeout_minutes=10
        ),
        AgentConfig(
            agent_id="agent_02",
            agent_name="Web Crawler",
            agent_path=project_root / "agent_02_web_crawler",
            script_name="run_crawler.py",
            dependencies=["agent_01"],
            required_inputs=["brand_channels.official_site_url"],
            output_tables=["raw_web_data"],
            timeout_minutes=60,
            memory_limit_mb=4096
        ),
        AgentConfig(
            agent_id="agent_03",
            agent_name="Instagram Crawler",
            agent_path=project_root / "agent_03_instagram_crawler",
            script_name="run_crawler.py",
            dependencies=["agent_01"],
            required_inputs=["brand_channels.instagram_handle"],
            output_tables=["raw_instagram_data"],
            timeout_minutes=45
        ),
        AgentConfig(
            agent_id="agent_04",
            agent_name="Naver Crawler",
            agent_path=project_root / "agent_04_naver_crawler",
            script_name="run_crawler.py",
            dependencies=["agent_01"],
            required_inputs=["brands.brand_official_name"],
            output_tables=["raw_naver_data"],
            timeout_minutes=30
        ),
        AgentConfig(
            agent_id="agent_05",
            agent_name="Tistory Crawler",
            agent_path=project_root / "agent_05_tistory_crawler",
            script_name="run_crawler.py",
            dependencies=["agent_01"],
            required_inputs=["brands.brand_official_name"],
            output_tables=["raw_tistory_data"],
            timeout_minutes=30
        ),
        AgentConfig(
            agent_id="agent_06",
            agent_name="Web Refiner",
            agent_path=project_root / "agent_06_web_refiner",
            script_name="run_refiner.py",
            dependencies=["agent_02"],
            required_inputs=["raw_web_data"],
            output_tables=["refined_content"],
            timeout_minutes=20
        ),
        AgentConfig(
            agent_id="agent_07",
            agent_name="Instagram Refiner",
            agent_path=project_root / "agent_07_instagram_refiner",
            script_name="run_instagram_refiner.py",
            dependencies=["agent_03"],
            required_inputs=["raw_instagram_data"],
            output_tables=["refined_content"],
            timeout_minutes=20
        ),
        AgentConfig(
            agent_id="agent_08",
            agent_name="Naver Refiner",
            agent_path=project_root / "agent_08_naver_refiner",
            script_name="run_naver_refiner.py",
            dependencies=["agent_04"],
            required_inputs=["raw_naver_data"],
            output_tables=["refined_content"],
            timeout_minutes=20
        ),
        AgentConfig(
            agent_id="agent_09",
            agent_name="Tistory Refiner",
            agent_path=project_root / "agent_09_tistory_refiner",
            script_name="run_tistory_refiner.py",
            dependencies=["agent_05"],
            required_inputs=["raw_tistory_data"],
            output_tables=["refined_content"],
            timeout_minutes=20
        ),
        AgentConfig(
            agent_id="agent_10",
            agent_name="Web Keyword Extractor",
            agent_path=project_root / "agent_10_web_keyword",
            script_name="main.py",
            dependencies=["agent_06"],
            required_inputs=["refined_content"],
            output_tables=["extracted_keywords"],
            timeout_minutes=15
        ),
        AgentConfig(
            agent_id="agent_11",
            agent_name="Social Keyword Extractor",
            agent_path=project_root / "agent_11_social_keyword",
            script_name="main.py",
            dependencies=["agent_07"],
            required_inputs=["refined_content"],
            output_tables=["extracted_keywords"],
            timeout_minutes=15
        ),
        AgentConfig(
            agent_id="agent_12",
            agent_name="Prompt Generator",
            agent_path=project_root / "agent_12_prompt_generator",
            script_name="main.py",
            dependencies=["agent_10", "agent_11"],
            required_inputs=["extracted_keywords"],
            output_tables=["generated_prompts"],
            timeout_minutes=10
        ),
        AgentConfig(
            agent_id="agent_13",
            agent_name="Web GEO Optimizer",
            agent_path=project_root / "agent_13_web_geo",
            script_name="main.py",
            dependencies=["agent_06"],
            required_inputs=["refined_content"],
            output_tables=["web_geo_analysis"],
            timeout_minutes=25
        ),
        AgentConfig(
            agent_id="agent_14",
            agent_name="Instagram GEO Optimizer",
            agent_path=project_root / "agent_14_instagram_geo",
            script_name="main.py",
            dependencies=["agent_07"],
            required_inputs=["refined_content"],
            output_tables=["instagram_geo_analysis"],
            timeout_minutes=25
        ),
        AgentConfig(
            agent_id="agent_15",
            agent_name="Blog GEO Analyzer",
            agent_path=project_root / "agent_15_blog_geo",
            script_name="run_analysis.py",
            dependencies=["agent_08", "agent_09"],
            required_inputs=["raw_naver_data", "raw_tistory_data"],
            output_tables=["blog_geo_analyses"],
            timeout_minutes=30
        )
    ]
    
    return configs

if __name__ == "__main__":
    # 테스트 실행
    from .logging_manager import create_agent_logger
    
    configs = get_default_agent_configs()
    dependency_manager = AgentDependencyManager(configs)
    
    print("실행 순서:")
    for i, agent_id in enumerate(dependency_manager.get_execution_order(), 1):
        agent = configs[next(j for j, c in enumerate(configs) if c.agent_id == agent_id)]
        print(f"{i:2d}. {agent.agent_name} ({agent_id})")
    
    # 개별 에이전트 실행 테스트
    # logger = create_agent_logger("test_agent", "Test Agent")
    # config = configs[0]  # agent_01
    # runner = AgentRunner(config, logger)
    # result = runner.execute(brand_id=1)
    # print(f"실행 결과: {result.success}")