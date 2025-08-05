"""
Database Schema for Blog GEO Analysis

Defines tables for storing blog analysis results.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, 
    ForeignKey, JSON, Boolean, Index, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class Platform(str, enum.Enum):
    """Supported blog platforms"""
    NAVER = "naver"
    TISTORY = "tistory"


class BlogGEOAnalysis(Base):
    """Main analysis record for a brand's blog content"""
    __tablename__ = 'blog_geo_analyses'
    
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, nullable=False, index=True)
    platform = Column(Enum(Platform), nullable=False)
    
    # Analysis configuration
    total_posts_analyzed = Column(Integer)
    posts_consulted = Column(Integer)
    n_selective = Column(Integer)  # Number of top/bottom posts selected
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # File paths
    analysis_report_path = Column(String(500))
    consulting_report_path = Column(String(500))
    
    # Overall metrics
    average_eeat_score = Column(Float)
    average_geo_score = Column(Float)
    average_synergy_score = Column(Float)
    overall_score = Column(Float)
    
    # Summary
    summary = Column(JSON)  # Strengths, weaknesses, key findings
    
    # Relationships
    post_analyses = relationship("BlogPostAnalysis", back_populates="analysis")
    consulting_reports = relationship("BlogConsultingReport", back_populates="analysis")
    
    # Indexes
    __table_args__ = (
        Index('idx_brand_platform_date', 'brand_id', 'platform', 'created_at'),
    )


class BlogPostAnalysis(Base):
    """Individual blog post analysis results"""
    __tablename__ = 'blog_post_analyses'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('blog_geo_analyses.id'))
    post_id = Column(String(100))  # Internal post identifier
    
    # Post metadata
    post_title = Column(Text)
    post_url = Column(Text)
    image_count = Column(Integer)
    
    # E-E-A-T scores (each out of 100)
    experience_score = Column(Float)
    expertise_score = Column(Float)
    authoritativeness_score = Column(Float)
    trustworthiness_score = Column(Float)
    
    # GEO scores (each out of 100)
    clarity_score = Column(Float)
    structure_score = Column(Float)
    context_score = Column(Float)
    alignment_score = Column(Float)
    originality_score = Column(Float)
    timeliness_score = Column(Float)
    
    # Synergy scores
    consistency_score = Column(Float)
    synergy_effect_score = Column(Float)
    
    # Overall
    average_score = Column(Float)
    
    # Detailed analysis
    eeat_analysis = Column(JSON)  # Full E-E-A-T evaluation
    geo_analysis = Column(JSON)   # Full GEO analysis
    synergy_analysis = Column(JSON)  # Synergy analysis
    
    # Summary
    strengths = Column(JSON)  # List of strengths
    weaknesses = Column(JSON)  # List of weaknesses
    
    # Relationships
    analysis = relationship("BlogGEOAnalysis", back_populates="post_analyses")


class BlogConsultingReport(Base):
    """Consulting reports for selected posts"""
    __tablename__ = 'blog_consulting_reports'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('blog_geo_analyses.id'))
    post_id = Column(String(100))
    
    # Selection info
    selection_type = Column(String(20))  # 'top' or 'bottom'
    original_score = Column(Float)
    
    # Consulting strategies
    title_consulting = Column(JSON)  # Title improvement strategies
    content_consulting = Column(JSON)  # Content improvement strategies
    synergy_consulting = Column(JSON)  # Synergy enhancement strategies
    
    # Generated content
    generated_title = Column(Text)
    generated_body = Column(Text)
    composite_image_idea = Column(Text)
    
    # Image paths
    dalle_image_path = Column(String(500))
    final_blog_image_path = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("BlogGEOAnalysis", back_populates="consulting_reports")


class BlogGEOBenchmark(Base):
    """Industry benchmarks for comparison"""
    __tablename__ = 'blog_geo_benchmarks'
    
    id = Column(Integer, primary_key=True)
    platform = Column(Enum(Platform), nullable=False)
    industry = Column(String(100))
    
    # Benchmark scores
    avg_eeat_score = Column(Float)
    avg_geo_score = Column(Float)
    avg_synergy_score = Column(Float)
    
    # Percentiles
    eeat_percentiles = Column(JSON)  # {25: score, 50: score, 75: score}
    geo_percentiles = Column(JSON)
    synergy_percentiles = Column(JSON)
    
    # Metadata
    sample_size = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Database utilities
def create_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Drop all tables"""
    Base.metadata.drop_all(engine)


def get_table_info():
    """Get information about all tables"""
    return {
        "tables": [
            {
                "name": "blog_geo_analyses",
                "description": "Main analysis records",
                "columns": BlogGEOAnalysis.__table__.columns.keys()
            },
            {
                "name": "blog_post_analyses",
                "description": "Individual post analysis results",
                "columns": BlogPostAnalysis.__table__.columns.keys()
            },
            {
                "name": "blog_consulting_reports",
                "description": "Consulting reports for selected posts",
                "columns": BlogConsultingReport.__table__.columns.keys()
            },
            {
                "name": "blog_geo_benchmarks",
                "description": "Industry benchmarks",
                "columns": BlogGEOBenchmark.__table__.columns.keys()
            }
        ]
    }