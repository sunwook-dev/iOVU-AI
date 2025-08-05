"""
KIJUN Instagram 순차 통합 파이프라인
- 파일별 순차 처리: 파일1 → 1→2→3단계 완료, 파일2 → 1→2→3단계 완료  
- 12개 게시물 전체 처리
- 실제 이미지 파일 사용 (images/ 폴더)
- JSON 콘텐츠 통합 (hashtags, new_caption_v1)
"""

from workflow.pipeline_manager import run_sequential_pipeline


def main(brand_name=None):
    """메인 실행 함수"""
    return run_sequential_pipeline(brand_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 전체 프로세스 오류: {e}")
        import traceback
        traceback.print_exc()
