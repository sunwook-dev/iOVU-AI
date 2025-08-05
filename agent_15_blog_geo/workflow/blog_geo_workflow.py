"""
Blog GEO Analysis Workflow

Main LangGraph workflow orchestration for blog analysis.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import BlogGEOWorkflowState
from .nodes.prepare_data import prepare_data_node
from .nodes.analyze_posts import analyze_posts_node
from .nodes.rank_and_select import rank_and_select_node
from .nodes.consult_posts import consult_posts_node
from .nodes.generate_images import generate_images_node
from .nodes.generate_blog_images import generate_blog_images_and_enhance_report_node
from .nodes.finalize_reports import finalize_reports_node


class BlogGEOWorkflow:
    """
    Blog GEO Analysis Workflow
    
    Implements the 2-stage process from the notebook:
    1. Analyze all posts with E-E-A-T and GEO
    2. Select top/bottom performers for deep consulting
    """
    
    def __init__(self):
        """Initialize the workflow graph"""
        self.workflow = None
        self.app = None
        self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        # Create workflow graph
        self.workflow = StateGraph(BlogGEOWorkflowState)
        
        # Add nodes
        self.workflow.add_node("prepare_data", prepare_data_node)
        self.workflow.add_node("analyze_posts", analyze_posts_node)
        self.workflow.add_node("rank_and_select", rank_and_select_node)
        self.workflow.add_node("consult_posts", consult_posts_node)
        self.workflow.add_node("generate_idea_images", generate_images_node)
        self.workflow.add_node("generate_blog_images_and_enhance_report", 
                              generate_blog_images_and_enhance_report_node)
        self.workflow.add_node("finalize_reports", finalize_reports_node)
        
        # Set entry point
        self.workflow.set_entry_point("prepare_data")
        
        # Add edges (linear flow)
        self.workflow.add_edge("prepare_data", "analyze_posts")
        self.workflow.add_edge("analyze_posts", "rank_and_select")
        self.workflow.add_edge("rank_and_select", "consult_posts")
        self.workflow.add_edge("consult_posts", "generate_idea_images")
        self.workflow.add_edge("generate_idea_images", "generate_blog_images_and_enhance_report")
        self.workflow.add_edge("generate_blog_images_and_enhance_report", "finalize_reports")
        self.workflow.add_edge("finalize_reports", END)
        
        # Compile the workflow
        self.app = self.workflow.compile()
    
    def run(self, initial_state: BlogGEOWorkflowState) -> Dict[str, Any]:
        """
        Run the workflow with initial state
        
        Args:
            initial_state: Initial workflow state
            
        Returns:
            Final workflow state
        """
        print(f"\n{'='*60}")
        print(f"<분석 시작> {initial_state['platform'].upper()} 블로그 분석")
        print(f"   브랜드: {initial_state['brand_name']} (ID: {initial_state['brand_id']})")
        print(f"   분석 포스트 수: {initial_state['total_posts_to_process'] or '전체'} 개")
        print(f"   선택 포스트: 상위 {initial_state['n_selective']}개 + 하위 {initial_state['n_selective']}개")
        print(f"{'='*60}")
        try:
            # Run the workflow
            final_state = self.app.invoke(initial_state)
            print(f"\n{'='*60}")
            print(f"<분석 완료> 1차 분석 및 컨설팅이 완료되었습니다.")
            print(f"{'='*60}")
            return final_state
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"[오류] 워크플로우 실행 중 오류 발생: {e}")
            print(f"{'='*60}")
            import traceback
            traceback.print_exc()
            # Return state with error
            if 'errors' not in initial_state:
                initial_state['errors'] = []
            initial_state['errors'].append({
                "workflow": "main",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return initial_state
    
    def get_graph_image(self):
        """
        Get workflow graph visualization
        
        Returns:
            Graph image or None
        """
        try:
            return self.app.get_graph().draw_mermaid_png()
        except:
            return None


def create_blog_geo_workflow() -> BlogGEOWorkflow:
    """
    Factory function to create workflow instance
    
    Returns:
        BlogGEOWorkflow instance
    """
    return BlogGEOWorkflow()