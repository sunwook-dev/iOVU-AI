"""
Blog GEO Analyzer

블로그 E-E-A-T 및 GEO 분석을 위한 메인 오케스트레이터
네이버와 티스토리 플랫폼을 지원합니다.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional, List, Literal

from .workflow.blog_geo_workflow import create_blog_geo_workflow
from .workflow.state import create_initial_state
from .database.queries import BlogGEOQueries


class BlogGEOAnalyzer:
    """
    블로그 GEO 분석을 위한 메인 클래스

    이 클래스는 전체 분석 프로세스를 조율합니다:
    1. 데이터베이스에서 블로그 데이터 로드
    2. E-E-A-T 및 GEO 기준으로 분석
    3. 상위/하위 성과자 선택
    4. 컨설팅 보고서 생성
    5. 최적화된 블로그 이미지 생성
    """

    def __init__(
        self, openai_api_key: Optional[str] = None, output_dir: str = "../outputs"
    ):
        """
        분석기 초기화

        Args:
            openai_api_key: OpenAI API 키
            output_dir: 출력 파일 디렉토리
        """
        # 로깅 설정
        self._setup_logging()

        # 데이터베이스 쿼리 객체
        self.db_queries = BlogGEOQueries()

        # OpenAI API 키 설정
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OpenAI API 키가 필요합니다. 환경변수 OPENAI_API_KEY를 설정하거나 인자로 전달하세요."
            )

        # 출력 디렉토리
        from pathlib import Path

        output_path = Path(output_dir)
        if not output_path.is_absolute():
            # Always resolve relative path from modular_agents directory
            current_file = Path(__file__)  # agent_15_blog_geo/blog_geo_analyzer.py
            modular_agents_dir = current_file.parent.parent  # Go up to modular_agents
            output_path = modular_agents_dir / output_dir.lstrip("../")  # Remove ../ prefix
        self.output_dir = str(output_path)
        os.makedirs(self.output_dir, exist_ok=True)

        # 워크플로우 생성
        self.workflow = create_blog_geo_workflow()

        self.logger = logging.getLogger(__name__)

    def analyze_blog(
        self,
        platform: Literal["naver", "tistory"],
        brand_id: int,
        brand_name: str = "",
        total_posts_to_process: Optional[int] = 10,
        n_selective: int = 2,
        save_to_database: bool = True,
    ) -> Dict[str, Any]:
        """
        브랜드의 블로그 분석 실행

        Args:
            platform: 블로그 플랫폼 ("naver" 또는 "tistory")
            brand_id: 분석할 브랜드 ID
            brand_name: 브랜드명 (선택사항)
            total_posts_to_process: 분석할 최대 포스트 수 (None이면 전체)
            n_selective: 컨설팅할 상위/하위 포스트 수
            save_to_database: 결과를 데이터베이스에 저장할지 여부

        Returns:
            분석 결과 딕셔너리
        """
        # 초기 상태 생성
        initial_state = create_initial_state(
            platform=platform,
            brand_id=brand_id,
            brand_name=brand_name,
            total_posts_to_process=total_posts_to_process,
            n_selective=n_selective,
            output_dir=self.output_dir,
        )

        # 워크플로우 실행
        start_time = datetime.utcnow()
        final_state = self.workflow.run(initial_state)
        end_time = datetime.utcnow()

        # 결과 처리
        results = self._process_results(final_state, start_time, end_time)

        # 요청 시 데이터베이스에 저장
        if save_to_database and results["success"]:
            self._save_to_database(platform, results)

        return results

    def _process_results(
        self, final_state: Dict[str, Any], start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """워크플로우 결과를 구조화된 형식으로 처리"""

        # 오류 확인
        errors = final_state.get("errors", [])
        success = len(errors) == 0 and len(final_state.get("final_reports", [])) > 0

        # 메트릭 계산
        all_analyses = final_state.get("all_analysis_results", [])
        valid_analyses = [
            a for a in all_analyses if "error" not in a and a.get("analysis_report")
        ]

        # 평균 점수 계산
        avg_scores = self._calculate_average_scores(valid_analyses)

        # 컨설팅 결과 추출
        consulting_results = self._extract_consulting_results(
            final_state.get("final_reports", [])
        )

        return {
            "success": success,
            "platform": final_state["platform"],
            "brand_id": final_state["brand_id"],
            "brand_name": final_state["brand_name"],
            "total_posts_analyzed": len(final_state.get("posts_to_analyze", [])),
            "valid_analyses": len(valid_analyses),
            "posts_consulted": len(consulting_results),
            "average_scores": avg_scores,
            "analysis_report_path": final_state.get("analysis_report_file"),
            "consulting_report_path": final_state.get("final_consulting_report_file"),
            "consulting_results": consulting_results,
            "processing_time": (end_time - start_time).total_seconds(),
            "errors": errors,
        }

    def _calculate_average_scores(self, analyses: List[Dict]) -> Dict[str, float]:
        """모든 분석에 대한 평균 점수 계산"""
        if not analyses:
            return {}

        total_eeat = 0
        total_geo = 0
        total_synergy = 0
        total_overall = 0
        count = 0

        for analysis in analyses:
            report = analysis.get("analysis_report", {})
            if not report:
                continue

            # E-E-A-T 평균
            eeat = report.get("eeat_evaluation", {})
            eeat_scores = [
                eeat.get("experience", {}).get("score", 0),
                eeat.get("expertise", {}).get("score", 0),
                eeat.get("authoritativeness", {}).get("score", 0),
                eeat.get("trustworthiness", {}).get("score", 0),
            ]
            if any(eeat_scores):
                total_eeat += sum(eeat_scores) / len(eeat_scores)

            # GEO 평균
            geo = report.get("geo_analysis", {})
            geo_scores = [
                geo.get("clarity_and_specificity", {}).get("score", 0),
                geo.get("structured_information", {}).get("score", 0),
                geo.get("contextual_richness", {}).get("score", 0),
                geo.get("visual_text_alignment", {}).get("score", 0),
                geo.get("originality", {}).get("score", 0),
                geo.get("timeliness_and_event_relevance", {}).get("score", 0),
            ]
            if any(geo_scores):
                total_geo += sum(geo_scores) / len(geo_scores)

            # 시너지 평균
            synergy = report.get("synergy_analysis", {})
            synergy_scores = [
                synergy.get("consistency", {}).get("score", 0),
                synergy.get("synergy_effect", {}).get("score", 0),
            ]
            if any(synergy_scores):
                total_synergy += sum(synergy_scores) / len(synergy_scores)

            # 전체
            total_overall += report.get("summary", {}).get("average_score", 0)
            count += 1

        if count == 0:
            return {}

        return {
            "eeat_average": round(total_eeat / count, 2),
            "geo_average": round(total_geo / count, 2),
            "synergy_average": round(total_synergy / count, 2),
            "overall_average": round(total_overall / count, 2),
        }

    def _extract_consulting_results(self, reports: List[Dict]) -> List[Dict]:
        """주요 컨설팅 결과 추출"""
        results = []

        for report in reports:
            if "error" in report.get("consulting_report", {}):
                continue

            result = {
                "post_id": report.get("id"),
                "original_score": report.get("average_score"),
                "generated_title": (
                    report.get("consulting_report", {})
                    .get("title_consulting", {})
                    .get("strategy_a", {})
                    .get("example_after")
                ),
                "dalle_image": (
                    report.get("consulting_report", {})
                    .get("content_consulting", {})
                    .get("after_image_file")
                ),
                "final_blog_image": (
                    report.get("consulting_report", {}).get("final_blog_image")
                ),
            }
            results.append(result)

        return results

    def _save_to_database(
        self, platform: Literal["naver", "tistory"], results: Dict[str, Any]
    ):
        """분석 결과를 데이터베이스에 저장"""
        try:
            # 분석 데이터 준비
            analysis_data = {
                "brand_id": results["brand_id"],
                "platform": platform,
                "total_posts_analyzed": results["total_posts_analyzed"],
                "posts_consulted": results["posts_consulted"],
                "n_selective": 2,  # 워크플로우 기본값
                "created_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "analysis_report_path": results["analysis_report_path"],
                "consulting_report_path": results["consulting_report_path"],
                "average_eeat_score": results["average_scores"].get("eeat_average"),
                "average_geo_score": results["average_scores"].get("geo_average"),
                "average_synergy_score": results["average_scores"].get(
                    "synergy_average"
                ),
                "overall_score": results["average_scores"].get("overall_average"),
                "summary": {
                    "processing_time": results["processing_time"],
                    "valid_analyses": results["valid_analyses"],
                },
            }

            # 데이터베이스에 저장
            analysis_id = self.db_queries.save_analysis_result(analysis_data)
            self.logger.info(
                f"✅ 분석 결과가 데이터베이스에 저장되었습니다. (ID: {analysis_id})"
            )

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 저장 중 오류: {e}")

    def get_analysis_history(
        self,
        brand_id: int,
        platform: Optional[Literal["naver", "tistory"]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """브랜드의 분석 이력 조회"""
        return self.db_queries.get_analysis_history(brand_id, platform, limit)

    def _setup_logging(self):
        """로깅 설정"""
        # 로그 디렉토리 생성
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)

        # 로거 설정
        logger = logging.getLogger("agent_15_blog_geo")
        logger.setLevel(logging.INFO)

        # 기존 핸들러 제거
        logger.handlers = []

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 파일 핸들러 (RotatingFileHandler)
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'blog_geo_{datetime.now().strftime("%Y%m%d")}.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


def create_blog_geo_analyzer(
    openai_api_key: Optional[str] = None, output_dir: str = "../outputs"
) -> BlogGEOAnalyzer:
    """
    분석기 인스턴스를 생성하는 팩토리 함수

    Args:
        openai_api_key: OpenAI API 키
        output_dir: 출력 디렉토리

    Returns:
        BlogGEOAnalyzer 인스턴스
    """
    return BlogGEOAnalyzer(openai_api_key=openai_api_key, output_dir=output_dir)
