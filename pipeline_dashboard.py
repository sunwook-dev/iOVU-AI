"""
파이프라인 대시보드 - Streamlit 애플리케이션
- 브랜드 정보 입력
- 전체 파이프라인 실행 및 모니터링
- 실시간 로그 및 진행 상황 표시
- 에러 처리 및 재시도
"""

import streamlit as st
import pandas as pd
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import queue
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 프로젝트 루트 경로 설정
import sys
import os
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipeline_orchestrator import (
    PipelineOrchestrator, PipelineConfig, PipelineStatus, 
    create_pipeline_orchestrator
)
from utils.logging_manager import LogEntry, AgentStatus
from utils.agent_manager import get_default_agent_configs
from database.utils.connection import get_db

# Agent 01 모듈 추가
sys.path.append('./agent_01_query_collector')
try:
    from agent_01_query_collector.models import BrandInput
    from agent_01_query_collector.collector_service import CollectorService
except ImportError:
    st.warning("⚠️ Agent 01 모듈을 찾을 수 없습니다. 새 브랜드 등록 기능이 제한될 수 있습니다.")

# 페이지 설정
st.set_page_config(
    page_title="Pipeline Dashboard - 모듈러 에이전트 파이프라인",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .agent-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #dee2e6;
    }
    .agent-card.running {
        border-left-color: #007bff;
        background-color: #e3f2fd;
    }
    .agent-card.completed {
        border-left-color: #28a745;
        background-color: #e8f5e9;
    }
    .agent-card.failed {
        border-left-color: #dc3545;
        background-color: #ffebee;
    }
    .log-container {
        background-color: #2b2b2b;
        color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        height: 400px;
        overflow-y: auto;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-pending { background-color: #6c757d; }
    .status-running { background-color: #007bff; }
    .status-completed { background-color: #28a745; }
    .status-failed { background-color: #dc3545; }
    .status-paused { background-color: #ffc107; }
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'pipeline_logs' not in st.session_state:
    st.session_state.pipeline_logs = []
if 'agent_progress' not in st.session_state:
    st.session_state.agent_progress = {}
if 'pipeline_status' not in st.session_state:
    st.session_state.pipeline_status = PipelineStatus.PENDING
if 'execution_start_time' not in st.session_state:
    st.session_state.execution_start_time = None

# 로그 큐 (실시간 로그 표시용)
if 'log_queue' not in st.session_state:
    st.session_state.log_queue = queue.Queue()

# 헤더
st.markdown('<h1 class="main-header">🚀 모듈러 에이전트 파이프라인 대시보드</h1>', unsafe_allow_html=True)

# 사이드바 - 파이프라인 설정
with st.sidebar:
    st.header("⚙️ 파이프라인 설정")
    
    # 브랜드 정보 입력 방식 선택
    st.subheader("📋 브랜드 정보")
    
    input_mode = st.radio(
        "입력 방식",
        ["새 브랜드 등록", "기존 브랜드 ID 사용"],
        help="새 브랜드를 등록하거나 기존 브랜드 ID를 사용할 수 있습니다"
    )
    
    if input_mode == "기존 브랜드 ID 사용":
        # 기존 방식: 브랜드 ID만 입력
        brand_id = st.number_input("브랜드 ID", min_value=1, value=1, step=1)
        brand_name = st.text_input("브랜드명 (선택)", placeholder="예: 나이키")
        
        # 브랜드 정보 확인
        if st.button("브랜드 정보 확인"):
            try:
                from database.queries.brand_queries import BrandQueries
                brand_info = BrandQueries.get_brand_by_id(brand_id)
                if brand_info:
                    st.success(f"✅ 브랜드 확인: {brand_info.get('brand_official_name', 'Unknown')}")
                else:
                    st.error(f"❌ 브랜드 ID {brand_id}를 찾을 수 없습니다")
            except Exception as e:
                st.error(f"브랜드 조회 실패: {str(e)}")
        
        # 새 브랜드 등록용 변수들 초기화
        new_brand_data = None
        
    else:
        # 새 브랜드 등록: Agent 01의 상세 입력 폼
        st.markdown("**새 브랜드를 등록하고 파이프라인을 실행합니다**")
        
        with st.form("new_brand_form"):
            # 필수 정보
            st.markdown("##### 필수 정보")
            brand_name = st.text_input(
                "브랜드명 *",
                placeholder="예: 나이키, 유니폼브릿지",
                help="정확한 브랜드 공식 명칭을 입력하세요"
            )
            
            col_country, col_price = st.columns(2)
            with col_country:
                country = st.selectbox(
                    "본사 국가",
                    ["KR", "US", "JP", "CN", "EU", "기타"],
                    index=0
                )
            with col_price:
                price_positioning = st.selectbox(
                    "가격대",
                    ["Value", "Mid-tier", "Premium", "Luxury"],
                    index=1
                )
            
            # 채널 정보
            st.markdown("##### 채널 정보")
            homepage_url = st.text_input(
                "홈페이지 URL",
                placeholder="https://example.com",
                help="https:// 포함하여 입력"
            )
            
            instagram = st.text_input(
                "Instagram 계정",
                placeholder="@brand_official 또는 brand_official",
                help="@ 기호는 자동으로 제거됩니다"
            )
            
            # 추가 정보 (축소된 버전)
            with st.expander("추가 정보 (선택)"):
                tagline = st.text_input(
                    "브랜드 슬로건",
                    placeholder="Just Do It"
                )
                
                story = st.text_area(
                    "브랜드 스토리",
                    placeholder="브랜드의 철학이나 역사를 간단히 설명해주세요",
                    height=80
                )
                
                categories = st.multiselect(
                    "카테고리",
                    ["패션", "뷰티", "라이프스타일", "스포츠", "테크", "F&B"],
                    default=[]
                )
                
                naver_url = st.text_input(
                    "네이버 쇼핑 URL",
                    placeholder="https://brand.shopping.naver.com/..."
                )
            
            # 브랜드 등록 버튼
            register_brand = st.form_submit_button("📝 브랜드 등록", type="primary")
        
        # 브랜드 등록 처리
        if register_brand:
            if not brand_name.strip():
                st.error("브랜드명은 필수 입력 항목입니다.")
                new_brand_data = None
            else:
                try:
                    # BrandInput 모델을 사용하여 검증 및 등록
                    
                    # 브랜드 입력 데이터 생성
                    brand_input = BrandInput(
                        name=brand_name.strip(),
                        country=country,
                        price_positioning=price_positioning,
                        homepage_url=homepage_url.strip() if homepage_url else None,
                        instagram=instagram.strip() if instagram else None,
                        tagline=tagline.strip() if tagline else None,
                        story=story.strip() if story else None,
                        categories=categories,
                        naver_url=naver_url.strip() if naver_url else None
                    )
                    
                    # 브랜드 등록
                    collector_service = CollectorService()
                    
                    # 검증
                    validation_errors = collector_service.validate_brand_input(brand_input)
                    if validation_errors:
                        for error in validation_errors:
                            st.error(f"{error.field}: {error.message}")
                        new_brand_data = None
                    else:
                        # 등록
                        with st.spinner("브랜드 등록 중..."):
                            response = collector_service.save_brand(brand_input)
                            brand_id = response.brand_id
                            
                            # 등록 성공
                            st.success(f"✅ {response.message} (ID: {brand_id})")
                            st.balloons()
                            
                            # 새 브랜드 데이터 설정
                            new_brand_data = {
                                'brand_id': brand_id,
                                'brand_name': brand_name,
                                'brand_input': brand_input
                            }
                            
                            # 세션에 저장
                            if 'new_brand_data' not in st.session_state:
                                st.session_state.new_brand_data = {}
                            st.session_state.new_brand_data = new_brand_data
                
                except Exception as e:
                    st.error(f"브랜드 등록 실패: {str(e)}")
                    new_brand_data = None
        
        # 등록된 브랜드 정보 표시
        if 'new_brand_data' in st.session_state and st.session_state.new_brand_data:
            brand_data = st.session_state.new_brand_data
            brand_id = brand_data['brand_id']
            st.info(f"등록된 브랜드: {brand_data['brand_name']} (ID: {brand_id})")
        else:
            brand_id = None
    
    # 실행 옵션
    st.subheader("🎯 실행 옵션")
    
    # 에이전트 선택
    agent_configs = get_default_agent_configs()
    all_agents = [(config.agent_id, config.agent_name) for config in agent_configs]
    
    execution_mode = st.radio(
        "실행 모드",
        ["전체 실행", "선택적 실행", "특정 단계부터"]
    )
    
    target_agents = None
    skip_agents = None
    
    if execution_mode == "선택적 실행":
        selected_agents = st.multiselect(
            "실행할 에이전트 선택",
            options=[aid for aid, _ in all_agents],
            format_func=lambda x: f"{x}: {next(name for aid, name in all_agents if aid == x)}",
            default=None
        )
        target_agents = selected_agents if selected_agents else None
    
    elif execution_mode == "특정 단계부터":
        start_from = st.selectbox(
            "시작 에이전트 선택",
            options=[aid for aid, _ in all_agents],
            format_func=lambda x: f"{x}: {next(name for aid, name in all_agents if aid == x)}"
        )
        if start_from:
            # 선택된 에이전트부터 끝까지
            start_index = next(i for i, (aid, _) in enumerate(all_agents) if aid == start_from)
            target_agents = [aid for aid, _ in all_agents[start_index:]]
    
    # 고급 옵션
    with st.expander("고급 옵션"):
        stop_on_error = st.checkbox("에러 시 중단", value=True)
        validate_data = st.checkbox("데이터 검증", value=True)
        auto_retry = st.checkbox("자동 재시도", value=True)
        
        # 건너뛸 에이전트
        skip_agent_list = st.multiselect(
            "건너뛸 에이전트",
            options=[aid for aid, _ in all_agents],
            format_func=lambda x: f"{x}: {next(name for aid, name in all_agents if aid == x)}"
        )
        skip_agents = skip_agent_list if skip_agent_list else None
    
    # 환경 변수
    with st.expander("환경 변수"):
        openai_api_key = st.text_input("OPENAI_API_KEY", type="password", help="OpenAI API 키")
        custom_env_vars = st.text_area(
            "추가 환경 변수 (JSON 형식)",
            placeholder='{"KEY": "value"}',
            help="JSON 형식으로 환경 변수 입력"
        )
    
    st.divider()
    
    # 현재 상태
    st.subheader("📊 현재 상태")
    
    status_colors = {
        PipelineStatus.PENDING: "🔵",
        PipelineStatus.RUNNING: "🟢",
        PipelineStatus.PAUSED: "🟡",
        PipelineStatus.COMPLETED: "✅",
        PipelineStatus.FAILED: "❌",
        PipelineStatus.CANCELLED: "⏹️"
    }
    
    current_status = st.session_state.pipeline_status
    st.markdown(f"**상태:** {status_colors.get(current_status, '❓')} {current_status.value}")
    
    if st.session_state.execution_start_time:
        elapsed = datetime.now() - st.session_state.execution_start_time
        st.markdown(f"**실행 시간:** {str(elapsed).split('.')[0]}")

# 메인 콘텐츠
tab1, tab2, tab3, tab4 = st.tabs(["🎮 제어판", "📊 진행 상황", "📝 로그", "📈 통계"])

with tab1:
    st.header("파이프라인 제어")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 브랜드 ID 유효성 검사
        can_start = brand_id is not None and brand_id > 0
        button_disabled = (st.session_state.pipeline_status == PipelineStatus.RUNNING) or not can_start
        
        if not can_start:
            st.warning("⚠️ 브랜드 정보를 먼저 입력하거나 확인하세요")
        
        if st.button("🚀 시작", type="primary", disabled=button_disabled):
            # 브랜드 ID 검증
            if not brand_id:
                st.error("❌ 브랜드 ID가 없습니다. 브랜드를 먼저 등록하거나 확인하세요.")
                st.stop()
            
            # 파이프라인 설정 생성
            env_vars = {}
            if openai_api_key:
                env_vars["OPENAI_API_KEY"] = openai_api_key
            
            if custom_env_vars:
                try:
                    custom_vars = json.loads(custom_env_vars)
                    env_vars.update(custom_vars)
                except json.JSONDecodeError:
                    st.error("환경 변수 JSON 형식이 잘못되었습니다")
                    st.stop()
            
            # 브랜드명 설정 (새 브랜드인 경우 자동 설정)
            final_brand_name = brand_name
            if input_mode == "새 브랜드 등록" and 'new_brand_data' in st.session_state:
                final_brand_name = st.session_state.new_brand_data.get('brand_name', brand_name)
            
            config = PipelineConfig(
                brand_id=brand_id,
                brand_name=final_brand_name or "",
                target_agents=target_agents,
                skip_agents=skip_agents,
                stop_on_error=stop_on_error,
                validate_data=validate_data,
                auto_retry=auto_retry,
                environment_vars=env_vars if env_vars else None
            )
            
            # 오케스트레이터 생성
            st.session_state.orchestrator = create_pipeline_orchestrator()
            
            # 콜백 설정
            def status_callback(status: PipelineStatus):
                st.session_state.pipeline_status = status
            
            def progress_callback(agent_id: str, progress: float):
                if 'agent_progress' not in st.session_state:
                    st.session_state.agent_progress = {}
                st.session_state.agent_progress[agent_id] = progress
            
            st.session_state.orchestrator.add_status_callback(status_callback)
            st.session_state.orchestrator.add_progress_callback(progress_callback)
            
            # 로그 구독
            def log_callback(log_entry: LogEntry):
                st.session_state.log_queue.put(log_entry)
            
            st.session_state.orchestrator.logging_manager.subscribe(log_callback)
            
            # 파이프라인 시작
            st.session_state.execution_start_time = datetime.now()
            result = st.session_state.orchestrator.execute_pipeline(config)
            
            st.success("파이프라인이 시작되었습니다!")
            st.rerun()
    
    with col2:
        if st.button("⏸️ 일시정지", disabled=(st.session_state.pipeline_status != PipelineStatus.RUNNING)):
            if st.session_state.orchestrator:
                st.session_state.orchestrator.pause_pipeline()
                st.info("파이프라인이 일시정지되었습니다")
                st.rerun()
    
    with col3:
        if st.button("▶️ 재개", disabled=(st.session_state.pipeline_status != PipelineStatus.PAUSED)):
            if st.session_state.orchestrator:
                st.session_state.orchestrator.resume_pipeline()
                st.info("파이프라인이 재개되었습니다")
                st.rerun()
    
    with col4:
        if st.button("⏹️ 중지", disabled=(st.session_state.pipeline_status not in [PipelineStatus.RUNNING, PipelineStatus.PAUSED])):
            if st.session_state.orchestrator:
                st.session_state.orchestrator.stop_pipeline()
                st.warning("파이프라인이 중지되었습니다")
                st.rerun()
    
    # 브랜드 정보 요약
    st.subheader("📋 브랜드 정보 요약")
    if brand_id and brand_id > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("브랜드 ID", brand_id)
            if input_mode == "새 브랜드 등록" and 'new_brand_data' in st.session_state:
                brand_data = st.session_state.new_brand_data
                st.metric("브랜드명", brand_data.get('brand_name', 'N/A'))
            elif brand_name:
                st.metric("브랜드명", brand_name)
        
        with col2:
            if input_mode == "새 브랜드 등록" and 'new_brand_data' in st.session_state:
                brand_input = st.session_state.new_brand_data.get('brand_input')
                if brand_input:
                    st.metric("본사 국가", brand_input.country)
                    st.metric("가격대", brand_input.price_positioning)
                    
                    # 채널 정보 표시
                    channels = []
                    if brand_input.homepage_url:
                        channels.append("🌐 웹사이트")
                    if brand_input.instagram:
                        channels.append("📷 Instagram")
                    if brand_input.naver_url:
                        channels.append("🛒 네이버쇼핑")
                    
                    if channels:
                        st.metric("채널", ", ".join(channels))
            else:
                st.info("기존 브랜드 ID 사용 중")
        
        # 상세 정보 표시 (새 브랜드인 경우)
        if input_mode == "새 브랜드 등록" and 'new_brand_data' in st.session_state:
            with st.expander("상세 브랜드 정보"):
                brand_input = st.session_state.new_brand_data.get('brand_input')
                if brand_input:
                    if brand_input.homepage_url:
                        st.text(f"홈페이지: {brand_input.homepage_url}")
                    if brand_input.instagram:
                        st.text(f"Instagram: @{brand_input.instagram}")
                    if brand_input.tagline:
                        st.text(f"슬로건: {brand_input.tagline}")
                    if brand_input.categories:
                        st.text(f"카테고리: {', '.join(brand_input.categories)}")
    else:
        st.warning("브랜드 정보가 없습니다. 사이드바에서 브랜드를 등록하거나 ID를 입력하세요.")
    
    # 실행 계획 표시
    if execution_mode != "전체 실행" or skip_agents:
        st.subheader("📋 실행 계획")
        
        # 실행될 에이전트 목록 표시
        planned_agents = []
        all_agent_ids = [config.agent_id for config in agent_configs]
        
        if target_agents:
            planned_agents = target_agents
        else:
            planned_agents = all_agent_ids
        
        if skip_agents:
            planned_agents = [aid for aid in planned_agents if aid not in skip_agents]
        
        for i, agent_id in enumerate(planned_agents):
            agent_config = next(config for config in agent_configs if config.agent_id == agent_id)
            st.write(f"{i+1}. **{agent_config.agent_name}** ({agent_id})")

with tab2:
    st.header("진행 상황")
    
    # 전체 진행률
    if st.session_state.orchestrator and st.session_state.pipeline_status in [PipelineStatus.RUNNING, PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
        status_data = st.session_state.orchestrator.get_status()
        
        if 'pipeline_result' in status_data and status_data['pipeline_result']:
            result = status_data['pipeline_result']
            
            # 메트릭 표시
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("전체 에이전트", result.get('total_agents', 0))
            with col2:
                st.metric("완료", result.get('completed_agents', 0))
            with col3:
                st.metric("실패", result.get('failed_agents', 0))
            with col4:
                progress = 0
                if result.get('total_agents', 0) > 0:
                    progress = (result.get('completed_agents', 0) / result.get('total_agents', 0)) * 100
                st.metric("진행률", f"{progress:.1f}%")
            
            # 진행률 바
            st.progress(progress / 100)
    
    # 에이전트별 상태
    st.subheader("📋 에이전트별 상태")
    
    if st.session_state.orchestrator:
        logging_stats = st.session_state.orchestrator.logging_manager.get_session_stats()
        agent_progress = logging_stats.get('agent_progress', {})
        
        for config in agent_configs:
            agent_id = config.agent_id
            progress_data = agent_progress.get(agent_id, {})
            
            status = progress_data.get('status', 'pending')
            progress_percent = progress_data.get('progress_percent', 0)
            
            # 상태별 스타일
            card_class = f"agent-card {status}"
            
            st.markdown(f"""
            <div class="{card_class}">
                <strong>{config.agent_name}</strong> ({agent_id})<br>
                <small>상태: {status} | 진행률: {progress_percent:.1f}%</small>
            </div>
            """, unsafe_allow_html=True)
            
            if progress_percent > 0:
                st.progress(progress_percent / 100, text=f"{progress_percent:.1f}%")

with tab3:
    st.header("실시간 로그")
    
    # 로그 레벨 필터
    col1, col2 = st.columns([3, 1])
    with col1:
        log_levels = st.multiselect(
            "로그 레벨 필터",
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default=["INFO", "WARNING", "ERROR", "CRITICAL"]
        )
    with col2:
        if st.button("🗑️ 로그 지우기"):
            st.session_state.pipeline_logs.clear()
            st.rerun()
    
    # 실시간 로그 업데이트
    try:
        while not st.session_state.log_queue.empty():
            log_entry = st.session_state.log_queue.get_nowait()
            st.session_state.pipeline_logs.append(log_entry)
            # 로그가 너무 많으면 오래된 것 제거
            if len(st.session_state.pipeline_logs) > 1000:
                st.session_state.pipeline_logs = st.session_state.pipeline_logs[-500:]
    except queue.Empty:
        pass
    
    # 로그 표시
    log_container = st.container()
    
    with log_container:
        filtered_logs = [
            log for log in st.session_state.pipeline_logs 
            if log.level in log_levels
        ]
        
        if filtered_logs:
            log_text = ""
            for log_entry in filtered_logs[-100:]:  # 최근 100개만 표시
                timestamp = log_entry.timestamp.split('T')[1].split('.')[0]  # HH:MM:SS만 표시
                color = {
                    "DEBUG": "#6c757d",
                    "INFO": "#17a2b8", 
                    "WARNING": "#ffc107",
                    "ERROR": "#dc3545",
                    "CRITICAL": "#6f42c1"
                }.get(log_entry.level, "#ffffff")
                
                log_text += f'<span style="color: {color};">[{timestamp}] {log_entry.level}</span> '
                log_text += f'<span style="color: #28a745;">{log_entry.agent_name}</span>: '
                log_text += f'<span style="color: #ffffff;">{log_entry.message}</span><br>'
            
            st.markdown(f'<div class="log-container">{log_text}</div>', unsafe_allow_html=True)
        else:
            st.info("로그가 없습니다. 파이프라인을 시작하면 실시간 로그가 표시됩니다.")
    
    # 자동 새로고침
    if st.session_state.pipeline_status == PipelineStatus.RUNNING:
        time.sleep(2)
        st.rerun()

with tab4:
    st.header("실행 통계")
    
    if st.session_state.orchestrator:
        stats = st.session_state.orchestrator.logging_manager.get_session_stats()
        
        # 기본 통계
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 로그 수", stats.get('total_logs', 0))
        with col2:
            st.metric("에러 수", stats.get('error_count', 0))
        with col3:
            st.metric("경고 수", stats.get('warning_count', 0))
        
        # 에이전트별 통계 차트
        agent_progress = stats.get('agent_progress', {})
        
        if agent_progress:
            # 에이전트별 상태 분포
            status_counts = {}
            for agent_data in agent_progress.values():
                status = agent_data.get('status', 'pending')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                fig_pie = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="에이전트 상태 분포"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # 에이전트별 에러/경고 수
            agent_names = []
            error_counts = []
            warning_counts = []
            
            for agent_id, data in agent_progress.items():
                config = next((c for c in agent_configs if c.agent_id == agent_id), None)
                if config:
                    agent_names.append(config.agent_name)
                    error_counts.append(data.get('error_count', 0))
                    warning_counts.append(data.get('warning_count', 0))
            
            if agent_names and (any(error_counts) or any(warning_counts)):
                fig_bar = go.Figure(data=[
                    go.Bar(name='에러', x=agent_names, y=error_counts),
                    go.Bar(name='경고', x=agent_names, y=warning_counts)
                ])
                fig_bar.update_layout(
                    title="에이전트별 에러/경고 수",
                    barmode='group',
                    xaxis_title="에이전트",
                    yaxis_title="개수"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    
    # 결과 내보내기
    if st.session_state.orchestrator and st.session_state.pipeline_status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
        if st.button("📊 결과 내보내기"):
            try:
                export_file = st.session_state.orchestrator.export_results()
                st.success(f"결과가 내보내졌습니다: {export_file}")
                
                # 다운로드 링크 제공
                with open(export_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                st.download_button(
                    label="📁 결과 파일 다운로드",
                    data=file_content,
                    file_name=f"pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"결과 내보내기 실패: {str(e)}")

# 푸터
st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        f"<p style='text-align: center; color: #666;'>Pipeline Dashboard | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        unsafe_allow_html=True
    )

# 자동 새로고침 (실행 중일 때만)
if st.session_state.pipeline_status == PipelineStatus.RUNNING:
    time.sleep(1)
    st.rerun()