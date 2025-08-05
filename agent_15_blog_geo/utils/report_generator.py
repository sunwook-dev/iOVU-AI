"""
Report Generator for Blog GEO Analysis

Generates various report formats from analysis results.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from pathlib import Path


class BlogGEOReportGenerator:
    """Generate reports in various formats"""

    def __init__(self, output_dir: str = "../outputs"):
        """
        Initialize report generator

        Args:
            output_dir: Directory for output files
        """
        output_path = Path(output_dir)
        if not output_path.is_absolute():
            # Always resolve relative path from modular_agents directory
            current_file = Path(__file__)  # agent_15_blog_geo/utils/report_generator.py
            modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
            output_path = modular_agents_dir / output_dir.lstrip("../")  # Remove ../ prefix
        self.output_dir = output_path
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary_report(
        self, analysis_results: Dict[str, Any], format: str = "markdown"
    ) -> str:
        """
        Generate summary report

        Args:
            analysis_results: Analysis results from BlogGEOAnalyzer
            format: Output format (markdown, html, text)

        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = analysis_results.get("platform", "blog")

        if format == "markdown":
            return self._generate_markdown_summary(
                analysis_results, timestamp, platform
            )
        elif format == "html":
            return self._generate_html_summary(analysis_results, timestamp, platform)
        else:
            return self._generate_text_summary(analysis_results, timestamp, platform)

    def _generate_markdown_summary(
        self, results: Dict[str, Any], timestamp: str, platform: str
    ) -> str:
        """Generate Markdown summary report"""

        output_path = self.output_dir / f"{platform}_summary_{timestamp}.md"

        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write(f"# {platform.upper()} 블로그 E-E-A-T + GEO 분석 요약\n\n")
            f.write(
                f"**브랜드:** {results.get('brand_name', 'Unknown')} "
                f"(ID: {results.get('brand_id')})\n"
            )
            f.write(f"**생성일시:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**플랫폼:** {platform.upper()}\n\n")

            # Overview
            f.write("## 전체 분석 개요\n\n")
            f.write(
                f"- **분석 포스트 수:** {results.get('total_posts_analyzed', 0)} 개\n"
            )
            f.write(f"- **유효 분석:** {results.get('valid_analyses', 0)} 개\n")
            f.write(f"- **컨설팅 대상:** {results.get('posts_consulted', 0)} 개\n")
            f.write(f"- **처리 시간:** {results.get('processing_time', 0):.2f}초\n\n")

            # Average Scores
            scores = results.get("average_scores", {})
            if scores:
                f.write("## 평균 점수\n\n")
                f.write("| 항목 | 점수 |\n")
                f.write("|---------|------|\n")
                f.write(f"| E-E-A-T | {scores.get('eeat_average', 0):.1f} |\n")
                f.write(f"| GEO | {scores.get('geo_average', 0):.1f} |\n")
                f.write(f"| 시너지 | {scores.get('synergy_average', 0):.1f} |\n")
                f.write(
                    f"| **종합** | **{scores.get('overall_average', 0):.1f}** |\n\n"
                )

            # Consulting Results
            consulting = results.get("consulting_results", [])
            if consulting:
                f.write("## 컨설팅 결과\n\n")
                for i, item in enumerate(consulting, 1):
                    f.write(f"### {i}. 포스트 ID: {item.get('post_id')}\n")
                    f.write(f"- **원점수:** {item.get('original_score')}\n")
                    f.write(f"- **생성 제목:** {item.get('generated_title', 'N/A')}\n")
                    if item.get("final_blog_image", "").endswith(".png"):
                        f.write(f"- **최종 이미지:** `{item['final_blog_image']}`\n")
                    f.write("\n")

            # File Paths
            f.write("## 결과 파일 경로\n\n")
            f.write(
                f"- **분석 리포트:** `{results.get('analysis_report_path', 'N/A')}`\n"
            )
            f.write(
                f"- **컨설팅 리포트:** `{results.get('consulting_report_path', 'N/A')}`\n"
            )

        return str(output_path)

    def _generate_html_summary(
        self, results: Dict[str, Any], timestamp: str, platform: str
    ) -> str:
        """Generate HTML summary report"""

        output_path = self.output_dir / f"{platform}_summary_{timestamp}.html"

        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{platform.upper()} 블로그 분석 요약</title>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ background-color: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .score {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
    </style>
</head>
<body>
    <h1>{platform.upper()} 블로그 E-E-A-T + GEO 분석 요약</h1>
    
    <div class="metric">
        <strong>브랜드:</strong> {results.get('brand_name', 'Unknown')} (ID: {results.get('brand_id')})<br>
        <strong>생성일시:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>플랫폼:</strong> {platform.upper()}
    </div>
    
    <h2>전체 분석 개요</h2>
    <table>
        <tr><th>항목</th><th>값</th></tr>
        <tr><td>분석 포스트 수</td><td>{results.get('total_posts_analyzed', 0)} 개</td></tr>
        <tr><td>유효 분석</td><td>{results.get('valid_analyses', 0)} 개</td></tr>
        <tr><td>컨설팅 대상</td><td>{results.get('posts_consulted', 0)} 개</td></tr>
        <tr><td>처리 시간</td><td>{results.get('processing_time', 0):.2f}초</td></tr>
    </table>
"""
        # Add scores if available
        scores = results.get("average_scores", {})
        if scores:
            html_content += """
    <h2>평균 점수</h2>
    <table>
        <tr><th>항목</th><th>점수</th></tr>
"""
            html_content += f"""
        <tr><td>E-E-A-T</td><td>{scores.get('eeat_average', 0):.1f}</td></tr>
        <tr><td>GEO</td><td>{scores.get('geo_average', 0):.1f}</td></tr>
        <tr><td>시너지</td><td>{scores.get('synergy_average', 0):.1f}</td></tr>
        <tr><td><strong>종합</strong></td><td class="score">{scores.get('overall_average', 0):.1f}</td></tr>
    </table>
"""
        html_content += """
</body>
</html>
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(output_path)

    def _generate_text_summary(
        self, results: Dict[str, Any], timestamp: str, platform: str
    ) -> str:
        """Generate plain text summary report"""

        output_path = self.output_dir / f"{platform}_summary_{timestamp}.txt"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"{platform.upper()} 블로그 E-E-A-T + GEO 분석 요약\n")
            f.write("=" * 50 + "\n\n")
            f.write(
                f"브랜드: {results.get('brand_name', 'Unknown')} (ID: {results.get('brand_id')})\n"
            )
            f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"플랫폼: {platform.upper()}\n\n")
            f.write("분석 개요\n")
            f.write("-" * 30 + "\n")
            f.write(f"분석 포스트 수: {results.get('total_posts_analyzed', 0)} 개\n")
            f.write(f"유효 분석: {results.get('valid_analyses', 0)} 개\n")
            f.write(f"컨설팅 대상: {results.get('posts_consulted', 0)} 개\n")
            f.write(f"처리 시간: {results.get('processing_time', 0):.2f}초\n\n")
            scores = results.get("average_scores", {})
            if scores:
                f.write("평균 점수\n")
                f.write("-" * 30 + "\n")
                f.write(f"E-E-A-T: {scores.get('eeat_average', 0):.1f}\n")
                f.write(f"GEO: {scores.get('geo_average', 0):.1f}\n")
                f.write(f"시너지: {scores.get('synergy_average', 0):.1f}\n")
                f.write(f"종합: {scores.get('overall_average', 0):.1f}\n")

        return str(output_path)

    def export_to_csv(
        self, analysis_report_path: str, output_filename: Optional[str] = None
    ) -> str:
        """
        Export analysis results to CSV

        Args:
            analysis_report_path: Path to analysis JSON file
            output_filename: Optional output filename

        Returns:
            Path to CSV file
        """
        # Load analysis data
        with open(analysis_report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Prepare data for DataFrame
        rows = []
        for item in data:
            if "error" in item:
                continue

            post = item.get("source_post", {})
            report = item.get("analysis_report", {})

            row = {
                "post_id": post.get("id"),
                "title": post.get("title"),
                "eeat_score": self._get_average_eeat(report),
                "geo_score": self._get_average_geo(report),
                "synergy_score": self._get_average_synergy(report),
                "overall_score": report.get("summary", {}).get("average_score", 0),
            }
            rows.append(row)

        # Create DataFrame and save
        df = pd.DataFrame(rows)

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"blog_analysis_export_{timestamp}.csv"

        output_path = self.output_dir / output_filename
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return str(output_path)

    def _get_average_eeat(self, report: Dict) -> float:
        """Calculate average E-E-A-T score"""
        eeat = report.get("eeat_evaluation", {})
        scores = [
            eeat.get("experience", {}).get("score", 0),
            eeat.get("expertise", {}).get("score", 0),
            eeat.get("authoritativeness", {}).get("score", 0),
            eeat.get("trustworthiness", {}).get("score", 0),
        ]
        return sum(scores) / len(scores) if scores else 0

    def _get_average_geo(self, report: Dict) -> float:
        """Calculate average GEO score"""
        geo = report.get("geo_analysis", {})
        scores = [
            geo.get("clarity_and_specificity", {}).get("score", 0),
            geo.get("structured_information", {}).get("score", 0),
            geo.get("contextual_richness", {}).get("score", 0),
            geo.get("visual_text_alignment", {}).get("score", 0),
            geo.get("originality", {}).get("score", 0),
            geo.get("timeliness_and_event_relevance", {}).get("score", 0),
        ]
        return sum(scores) / len(scores) if scores else 0

    def _get_average_synergy(self, report: Dict) -> float:
        """Calculate average synergy score"""
        synergy = report.get("synergy_analysis", {})
        scores = [
            synergy.get("consistency", {}).get("score", 0),
            synergy.get("synergy_effect", {}).get("score", 0),
        ]
        return sum(scores) / len(scores) if scores else 0
