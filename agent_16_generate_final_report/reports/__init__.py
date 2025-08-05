"""
Report generation module
"""

from .llm_generator import generate_text_with_llm
from .report_generator import create_comprehensive_report

__all__ = [
    'generate_text_with_llm',
    'create_comprehensive_report'
]
