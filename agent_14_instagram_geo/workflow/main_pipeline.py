"""
KIJUN Instagram 완전 통합 파이프라인
"""
import os
from dotenv import load_dotenv
from workflow.pipeline_manager import run_sequential_pipeline


class KijunInstagramPipeline:
    def __init__(self):
        load_dotenv()
    
    def run_complete_pipeline(self):
        """완전한 파이프라인 실행"""
        return run_sequential_pipeline()
