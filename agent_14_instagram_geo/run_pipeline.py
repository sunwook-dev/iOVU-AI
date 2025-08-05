# -*- coding: utf-8 -*-
"""
Instagram 통합 파이프라인 실행기
사용법: python run_pipeline.py {brand_official_name}
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
import kijun_sequential_pipeline


def main():
    """메인 실행 함수"""
    try:
        # 명령행 인수 확인
        if len(sys.argv) < 2:
            print("사용법: python run_pipeline.py {brand_official_name}")
            print("예시: python run_pipeline.py kijun")
            print("예시: python run_pipeline.py uniform_bridge")
            return 1
        
        brand_name = sys.argv[1]
        
        print(f"{brand_name.upper()} Instagram 순차 통합 파이프라인 실행")
        print("=" * 60)
        
        # 브랜드명을 파라미터로 전달하여 순차 통합 파이프라인 실행
        success = kijun_sequential_pipeline.main(brand_name)
        
        if success:
            print(f"\n{brand_name} 파이프라인이 성공적으로 완료되었습니다!")
            return 0
        else:
            print(f"\n{brand_name} 파이프라인 실행 중 오류가 발생했습니다.")
            return 1
            
    except Exception as e:
        print(f"전체 프로세스 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
