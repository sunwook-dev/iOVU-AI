#!/usr/bin/env python3
"""
브랜드 파이프라인 통합 실행 스크립트

FastAPI로 입력받은 브랜드명을 기억하여 모든 에이전트에 전달하고 순차적으로 실행합니다.

사용법:
    python run_brand_pipeline.py kijun
    python run_brand_pipeline.py "uniform bridge" --skip-crawlers
    python run_brand_pipeline.py kijun --agents 1,2,3,6,7,10
"""

import os
import sys
import asyncio
import argparse
import subprocess
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.queries.brand_queries import BrandQueries
from database.utils.connection import get_db

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrandPipelineRunner:
    """브랜드 파이프라인 실행 관리자"""
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.brand_id = None
        self.brand_data = None
        self.start_time = datetime.now()
        self.results = {}
        
    def setup_brand(self) -> bool:
        """브랜드 정보 설정 및 확인"""
        try:
            # 1. 데이터베이스에서 브랜드 조회
            logger.info(f"🔍 브랜드 '{self.brand_name}' 조회 중...")
            
            brand = BrandQueries.get_brand_by_name(self.brand_name)
            if not brand:
                logger.warning(f"❌ 브랜드 '{self.brand_name}'를 찾을 수 없습니다.")
                
                # Agent 01 API 서버 확인
                if self.check_api_server():
                    logger.info("📝 새 브랜드를 등록하시겠습니까? (Agent 01 API 사용)")
                    return False
                else:
                    logger.error("❌ Agent 01 API 서버가 실행되지 않았습니다.")
                    logger.info("💡 다음 명령어로 API 서버를 시작하세요:")
                    logger.info("   python agent_01_query_collector/run_api.py")
                    return False
            
            self.brand_data = brand

            logger.info(f"✅ 브랜드 정보 확인됨:")
            logger.info(f"   - 이름: {self.brand_name}")
            logger.info(f"   - 홈페이지: {self.brand_data.get('official_site_url', 'N/A')}")
            logger.info(f"   - Instagram: {self.brand_data.get('instagram_handle', 'N/A')}")

            # 환경 변수 설정
            os.environ['CURRENT_BRAND_NAME'] = self.brand_name

            return True
            
        except Exception as e:
            logger.error(f"❌ 브랜드 설정 중 오류: {e}")
            return False
    
    def check_api_server(self) -> bool:
        """Agent 01 API 서버 상태 확인"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def register_brand_via_api(self) -> bool:
        """Agent 01 API를 통해 브랜드 등록"""
        try:
            logger.info(f"📝 브랜드 '{self.brand_name}' 등록 중...")
            
            # 기본 브랜드 정보로 등록
            brand_data = {
                "name": self.brand_name,
                "country": "KR",  # 기본값
                "homepage_url": input("홈페이지 URL (선택): ").strip() or None,
                "instagram": input("Instagram 계정 (선택): ").strip() or None
            }
            
            response = requests.post(
                "http://localhost:8000/brands",
                json=brand_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.brand_id = result['brand_id']
                logger.info(f"✅ 브랜드 등록 성공! (ID: {self.brand_id})")
                return self.setup_brand()  # 등록 후 다시 설정
            else:
                logger.error(f"❌ 브랜드 등록 실패: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API 통신 오류: {e}")
            return False
    
    def run_agent(self, agent_id: str, agent_config: Dict) -> bool:
        """개별 에이전트 실행"""
        try:
            agent_name = agent_config['name']
            agent_path = PROJECT_ROOT / agent_config['path']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🚀 {agent_name} 실행 시작")
            logger.info(f"{'='*60}")
            
            # 실행 명령어 구성
            cmd = self.build_agent_command(agent_id, agent_config)
            
            # 에이전트 실행
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=agent_path,
                capture_output=True,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            # 결과 저장
            self.results[agent_id] = {
                'success': result.returncode == 0,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if result.returncode == 0:
                logger.info(f"✅ {agent_name} 완료 ({execution_time:.2f}초)")
                return True
            else:
                logger.error(f"❌ {agent_name} 실패 (코드: {result.returncode})")
                if result.stderr:
                    logger.error(f"에러: {result.stderr[:500]}...")
                return False
                
        except Exception as e:
            logger.error(f"❌ 에이전트 실행 오류: {e}")
            return False
    
    def build_agent_command(self, agent_id: str, agent_config: Dict) -> List[str]:
        """에이전트별 실행 명령어 생성 (brand_official_name만 사용)"""
        cmd = [sys.executable]

        if agent_id == 'agent_02':
            # Agent 02: 웹 크롤러 - URL 필요
            if not self.brand_data.get('official_site_url'):
                logger.warning("⚠️  홈페이지 URL이 없어 Agent 02를 건너뜁니다.")
                return None
            cmd.extend([
                "run_crawler.py",
                self.brand_data['official_site_url'],
                "--brand-name", self.brand_name
            ])

        elif agent_id == 'agent_03':
            # Agent 03: Instagram 크롤러
            if not self.brand_data.get('instagram_handle'):
                logger.warning("⚠️  Instagram 계정이 없어 Agent 03을 건너뜁니다.")
                return None
            cmd.extend([
                "run_crawler.py",
                "--brand-name", self.brand_name
            ])

        elif agent_id in ['agent_04', 'agent_05']:
            # Agent 04, 05: 블로그 크롤러
            cmd.extend([
                "run_crawler.py",
                "--brand-name", self.brand_name
            ])

        elif agent_id in ['agent_06', 'agent_07', 'agent_08', 'agent_09']:
            # Refiner 에이전트들
            cmd.extend([
                agent_config.get('script', 'run_refiner.py'),
                "--brand-name", self.brand_name
            ])

        elif agent_id in ['agent_10', 'agent_11']:
            # 키워드 추출 에이전트
            cmd.extend([
                agent_config.get('script', 'run_keyword_extractor.py'),
                "--brand-name", self.brand_name
            ])

        else:
            # 기타 에이전트
            cmd.extend([
                agent_config.get('script', 'main.py'),
                "--brand-name", self.brand_name
            ])

        return cmd
    
    def run_pipeline(self, target_agents: Optional[List[str]] = None, 
                     skip_crawlers: bool = False) -> bool:
        """전체 파이프라인 실행"""
        
        # 에이전트 설정
        agent_configs = {
            'agent_02': {'name': 'Agent 02: Web Crawler', 'path': 'agent_02_web_crawler'},
            'agent_03': {'name': 'Agent 03: Instagram Crawler', 'path': 'agent_03_instagram_crawler'},
            'agent_04': {'name': 'Agent 04: Naver Crawler', 'path': 'agent_04_naver_crawler'},
            'agent_05': {'name': 'Agent 05: Tistory Crawler', 'path': 'agent_05_tistory_crawler'},
            'agent_06': {'name': 'Agent 06: Web Refiner', 'path': 'agent_06_web_refiner'},
            'agent_07': {'name': 'Agent 07: Instagram Refiner', 'path': 'agent_07_instagram_refiner'},
            'agent_08': {'name': 'Agent 08: Naver Refiner', 'path': 'agent_08_naver_refiner'},
            'agent_09': {'name': 'Agent 09: Tistory Refiner', 'path': 'agent_09_tistory_refiner'},
            'agent_10': {'name': 'Agent 10: Web Keyword', 'path': 'agent_10_web_keyword'},
            'agent_11': {'name': 'Agent 11: Social Keyword', 'path': 'agent_11_social_keyword'},
        }
        
        # 실행할 에이전트 결정
        if target_agents:
            agents_to_run = [f"agent_{int(a):02d}" for a in target_agents]
        elif skip_crawlers:
            agents_to_run = ['agent_06', 'agent_07', 'agent_08', 'agent_09', 'agent_10', 'agent_11']
        else:
            agents_to_run = list(agent_configs.keys())
        
        logger.info(f"\n🎯 실행할 에이전트: {', '.join(agents_to_run)}")
        
        # 순차적으로 에이전트 실행
        success_count = 0
        fail_count = 0
        
        for agent_id in agents_to_run:
            if agent_id not in agent_configs:
                logger.warning(f"⚠️  알 수 없는 에이전트: {agent_id}")
                continue
                
            success = self.run_agent(agent_id, agent_configs[agent_id])
            if success:
                success_count += 1
            else:
                fail_count += 1
                # 실패 시 계속할지 확인
                if fail_count > 0:
                    response = input("\n계속 진행하시겠습니까? (y/n): ")
                    if response.lower() != 'y':
                        break
        
        # 최종 결과 출력
        total_time = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 파이프라인 실행 완료")
        logger.info(f"{'='*60}")
        logger.info(f"총 실행 시간: {total_time:.2f}초")
        logger.info(f"성공: {success_count}, 실패: {fail_count}")
        
        return fail_count == 0


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="브랜드 파이프라인 통합 실행"
    )
    parser.add_argument(
        "brand_name",
        help="처리할 브랜드명 (예: kijun, 'uniform bridge')"
    )
    parser.add_argument(
        "--agents",
        help="실행할 에이전트 번호 (쉼표로 구분, 예: 2,3,6,7)",
        default=None
    )
    parser.add_argument(
        "--skip-crawlers",
        action="store_true",
        help="크롤러 에이전트(2-5) 건너뛰기"
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="브랜드가 없으면 자동으로 등록"
    )
    
    args = parser.parse_args()
    
    # 파이프라인 실행
    runner = BrandPipelineRunner(args.brand_name)
    
    # 브랜드 설정
    if not runner.setup_brand():
        if args.register or input("\n새 브랜드를 등록하시겠습니까? (y/n): ").lower() == 'y':
            if not runner.register_brand_via_api():
                logger.error("❌ 브랜드 등록에 실패했습니다.")
                sys.exit(1)
        else:
            logger.info("파이프라인을 종료합니다.")
            sys.exit(0)
    
    # 에이전트 목록 파싱
    target_agents = None
    if args.agents:
        target_agents = [int(a.strip()) for a in args.agents.split(',')]
    
    # 파이프라인 실행
    success = runner.run_pipeline(
        target_agents=target_agents,
        skip_crawlers=args.skip_crawlers
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()