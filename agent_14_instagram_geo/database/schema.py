"""
Instagram GEO Analysis Database Schema

Database schema for storing Instagram GEO analysis results,
including E-E-A-T scores, GEO optimization results, and comprehensive analysis data.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class InstagramGEOAnalysis(Base):
    """
    Main table for storing Instagram GEO analysis results
    """
    __tablename__ = 'instagram_geo_analyses'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, nullable=False)
    brand_name = Column(String(255))
    business_type = Column(String(100))
    
    # Analysis configuration
    analysis_mode = Column(String(50))  # 'analyze', 'optimize', 'full'
    posts_analyzed = Column(Integer)
    max_posts_requested = Column(Integer)
    
    # Overall scores
    overall_geo_score = Column(Float)
    overall_eeat_score = Column(Float)
    overall_score = Column(Float)
    
    # E-E-A-T category averages
    experience_avg_score = Column(Float)
    expertise_avg_score = Column(Float)
    authoritativeness_avg_score = Column(Float)
    trustworthiness_avg_score = Column(Float)
    
    # GEO category averages  
    geo_clarity_avg_score = Column(Float)
    geo_structure_avg_score = Column(Float)
    geo_context_avg_score = Column(Float)
    geo_alignment_avg_score = Column(Float)
    geo_timeliness_avg_score = Column(Float)
    geo_originality_avg_score = Column(Float)
    
    # Visual analysis scores
    visual_consistency_score = Column(Float)
    brand_consistency_score = Column(Float)
    composition_quality_score = Column(Float)
    
    # Synergy analysis scores
    synergy_overall_score = Column(Float)
    narrative_synergy_score = Column(Float)
    visual_synergy_score = Column(Float)
    hashtag_synergy_score = Column(Float)
    
    # Analysis metadata
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_seconds = Column(Float)
    success_status = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # JSON fields for complex data
    key_insights = Column(JSON)  # List of key insights
    improvement_priorities = Column(JSON)  # List of improvement areas
    recommendations = Column(JSON)  # List of recommendations
    processing_stats = Column(JSON)  # Processing statistics
    
    # Relationships
    individual_analyses = relationship("PostEEATGEOScore", back_populates="analysis")
    optimization_results = relationship("GEOOptimizationResult", back_populates="analysis")
    visual_analyses = relationship("VisualAnalysisResult", back_populates="analysis")
    synergy_analyses = relationship("SynergyAnalysisResult", back_populates="analysis")
    generated_content = relationship("GeneratedInstagramContent", back_populates="analysis")
    
    def __repr__(self):
        return f"<InstagramGEOAnalysis(id={self.id}, brand_id={self.brand_id}, score={self.overall_score})>"


class PostEEATGEOScore(Base):
    """
    Individual post E-E-A-T and GEO scores
    """
    __tablename__ = 'post_eeat_geo_scores'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('instagram_geo_analyses.id'), nullable=False)
    post_id = Column(String(255))  # Instagram post ID
    post_url = Column(String(500))
    
    # Post metadata
    post_type = Column(String(50))  # 'photo', 'video', 'carousel', 'reel'
    caption = Column(Text)
    hashtags = Column(JSON)  # List of hashtags
    image_urls = Column(JSON)  # List of image URLs
    video_url = Column(String(500))
    post_timestamp = Column(DateTime)
    
    # E-E-A-T Scores (0-100)
    experience_score = Column(Float)
    expertise_score = Column(Float) 
    authoritativeness_score = Column(Float)
    trustworthiness_score = Column(Float)
    eeat_average_score = Column(Float)
    
    # GEO Scores (0-100)
    geo_clarity_score = Column(Float)
    geo_structure_score = Column(Float)
    geo_context_score = Column(Float)
    geo_alignment_score = Column(Float)
    geo_timeliness_score = Column(Float)
    geo_originality_score = Column(Float)
    geo_average_score = Column(Float)
    
    # Composite scores
    overall_average_score = Column(Float)
    
    # Engagement metrics
    likes_count = Column(Integer)
    comments_count = Column(Integer)
    shares_count = Column(Integer)
    saves_count = Column(Integer)
    engagement_rate = Column(Float)
    
    # Analysis details (JSON)
    eeat_analysis_details = Column(JSON)  # Detailed E-E-A-T analysis results
    geo_analysis_details = Column(JSON)   # Detailed GEO analysis results
    identified_themes = Column(JSON)      # Content themes identified
    improvement_suggestions = Column(JSON) # Specific improvement suggestions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("InstagramGEOAnalysis", back_populates="individual_analyses")
    
    def __repr__(self):
        return f"<PostEEATGEOScore(post_id={self.post_id}, overall_score={self.overall_average_score})>"


class GEOOptimizationResult(Base):
    """
    GEO optimization results for posts
    """
    __tablename__ = 'geo_optimization_results'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('instagram_geo_analyses.id'), nullable=False)
    post_id = Column(String(255))
    
    # Original content
    original_caption = Column(Text)
    original_hashtags = Column(JSON)
    
    # Optimized content
    optimized_caption_structure = Column(JSON)  # Hook, main content, CTA structure
    optimized_hashtags = Column(JSON)
    improvements_applied = Column(JSON)  # List of improvements made
    
    # Optimization metrics
    expected_score_improvement = Column(Float)
    optimization_reason = Column(Text)
    weak_areas_addressed = Column(JSON)  # Areas that were improved
    
    # Hashtag strategy
    hashtag_strategy = Column(JSON)  # Comprehensive hashtag recommendations
    hashtag_categories = Column(JSON)  # Brand, product, trend, etc.
    hashtag_performance_predictions = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("InstagramGEOAnalysis", back_populates="optimization_results")
    
    def __repr__(self):
        return f"<GEOOptimizationResult(post_id={self.post_id}, improvement={self.expected_score_improvement})>"


class VisualAnalysisResult(Base):
    """
    Visual content analysis results
    """
    __tablename__ = 'visual_analysis_results'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('instagram_geo_analyses.id'), nullable=False)
    
    # Brand consistency scores
    brand_consistency_overall_score = Column(Float)
    logo_usage_consistency = Column(Float)
    color_theme_consistency = Column(Float)
    style_consistency = Column(Float)
    filter_consistency = Column(Float)
    
    # Composition quality scores
    composition_average_score = Column(Float)
    rule_of_thirds_usage = Column(Float)
    proper_lighting = Column(Float)
    clear_subject_focus = Column(Float)
    balanced_composition = Column(Float)
    professional_quality = Column(Float)
    
    # Visual-text alignment
    visual_text_alignment_score = Column(Float)
    caption_image_relevance = Column(Float)
    hashtag_visual_match = Column(Float)
    text_readability = Column(Float)
    visual_storytelling = Column(Float)
    
    # Color analysis
    color_consistency_score = Column(Float)
    dominant_color_theme = Column(String(100))
    color_theme_distribution = Column(JSON)
    
    # Feed aesthetic
    feed_aesthetic_score = Column(Float)
    post_type_variety = Column(Float)
    visual_brand_strength = Column(Float)
    
    # Analysis details
    posts_analyzed = Column(Integer)
    high_quality_posts = Column(Integer)
    improvement_needed_posts = Column(Integer)
    visual_patterns = Column(JSON)
    brand_elements_detected = Column(JSON)
    
    # Recommendations
    visual_recommendations = Column(JSON)
    priority_improvements = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("InstagramGEOAnalysis", back_populates="visual_analyses")
    
    def __repr__(self):
        return f"<VisualAnalysisResult(brand_consistency={self.brand_consistency_overall_score})>"


class SynergyAnalysisResult(Base):
    """
    Post synergy analysis results
    """
    __tablename__ = 'synergy_analysis_results'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('instagram_geo_analyses.id'), nullable=False)
    
    # Overall synergy scores
    overall_synergy_score = Column(Float)
    synergy_grade = Column(String(10))  # A+, A, B+, B, C+, C
    
    # Component synergy scores
    narrative_synergy_score = Column(Float)
    visual_synergy_score = Column(Float)
    hashtag_synergy_score = Column(Float)
    engagement_synergy_score = Column(Float)
    theme_synergy_score = Column(Float)
    
    # Narrative analysis
    narrative_flow_score = Column(Float)
    theme_consistency_score = Column(Float)
    sequential_coherence = Column(Float)
    story_connections = Column(JSON)
    narrative_patterns = Column(JSON)
    
    # Visual synergy details
    visual_consistency_score = Column(Float)
    color_harmony_score = Column(Float)
    composition_coherence_score = Column(Float)
    feed_aesthetic_score = Column(Float)
    
    # Hashtag synergy
    hashtag_diversity_score = Column(Float)
    brand_hashtag_consistency = Column(Float)
    strategic_hashtag_usage = Column(Float)
    recurring_hashtags = Column(JSON)
    hashtag_category_distribution = Column(JSON)
    
    # Engagement synergy
    average_engagement = Column(Float)
    average_engagement_rate = Column(Float)
    engagement_consistency_score = Column(Float)
    high_performer_count = Column(Integer)
    low_performer_count = Column(Integer)
    engagement_trends = Column(JSON)
    
    # Content theme analysis
    content_theme_consistency = Column(Float)
    dominant_themes = Column(JSON)
    theme_distribution = Column(JSON)
    content_variety_score = Column(Float)
    
    # Best performing sequences
    best_sequences = Column(JSON)  # High-performing post sequences
    sequence_success_factors = Column(JSON)
    
    # Improvement opportunities
    synergy_recommendations = Column(JSON)
    improvement_priorities = Column(JSON)
    narrative_gaps = Column(JSON)
    
    # Analysis metadata
    posts_analyzed = Column(Integer)
    sequences_identified = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("InstagramGEOAnalysis", back_populates="synergy_analyses")
    
    def __repr__(self):
        return f"<SynergyAnalysisResult(synergy_score={self.overall_synergy_score}, grade={self.synergy_grade})>"


class GeneratedInstagramContent(Base):
    """
    Generated content for Instagram optimization
    """
    __tablename__ = 'generated_instagram_content'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('instagram_geo_analyses.id'), nullable=False)
    
    # FAQ Content
    instagram_faqs = Column(JSON)  # Generated FAQ content
    faq_count = Column(Integer)
    
    # Story content suggestions
    story_content_suggestions = Column(JSON)
    story_content_count = Column(Integer)
    
    # Bio optimization
    current_bio = Column(Text)
    optimized_bio = Column(Text)
    bio_improvements = Column(JSON)
    bio_optimization_score = Column(Float)
    bio_hashtags = Column(JSON)
    
    # Story highlights suggestions
    highlight_suggestions = Column(JSON)
    highlight_count = Column(Integer)
    
    # Content theme recommendations
    content_themes = Column(JSON)
    theme_count = Column(Integer)
    
    # Posting schedule optimization
    optimal_posting_schedule = Column(JSON)
    recommended_posting_times = Column(JSON)
    recommended_posting_days = Column(JSON)
    optimal_frequency = Column(String(100))
    
    # Content strategy recommendations
    content_strategy_summary = Column(JSON)
    next_steps = Column(JSON)
    immediate_actions = Column(JSON)
    
    # Performance predictions
    expected_engagement_improvement = Column(Float)
    predicted_reach_increase = Column(Float)
    content_quality_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("InstagramGEOAnalysis", back_populates="generated_content")
    
    def __repr__(self):
        return f"<GeneratedInstagramContent(faqs={self.faq_count}, themes={self.theme_count})>"


class InstagramGEOReport(Base):
    """
    Generated reports for Instagram GEO analysis
    """
    __tablename__ = 'instagram_geo_reports'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('instagram_geo_analyses.id'), nullable=False)
    
    # Report metadata
    report_type = Column(String(100))  # 'full', 'summary', 'executive'
    report_format = Column(String(50))  # 'json', 'pdf', 'html', 'markdown'
    report_title = Column(String(255))
    
    # Report content
    executive_summary = Column(Text)
    key_findings = Column(JSON)
    detailed_analysis = Column(JSON)
    recommendations = Column(JSON)
    action_plan = Column(JSON)
    
    # Performance metrics summary
    performance_overview = Column(JSON)
    score_breakdown = Column(JSON)
    improvement_tracking = Column(JSON)
    
    # Visual elements
    charts_data = Column(JSON)  # Data for generating charts
    infographic_elements = Column(JSON)
    
    # Export information
    file_path = Column(String(500))  # Path to exported file
    file_size_bytes = Column(Integer)
    export_status = Column(String(50))  # 'pending', 'completed', 'failed'
    
    # Access control
    is_public = Column(Boolean, default=False)
    access_token = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<InstagramGEOReport(id={self.id}, type={self.report_type}, status={self.export_status})>"


class HashtagPerformanceTracking(Base):
    """
    Track hashtag performance across analyses
    """
    __tablename__ = 'hashtag_performance_tracking'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, nullable=False)
    hashtag = Column(String(255), nullable=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    first_used_date = Column(DateTime)
    last_used_date = Column(DateTime)
    
    # Performance metrics
    average_engagement = Column(Float)
    average_reach = Column(Float)
    average_impressions = Column(Float)
    performance_score = Column(Float)
    
    # Category and analysis
    hashtag_category = Column(String(100))  # 'brand', 'product', 'trend', 'community'
    trending_status = Column(String(50))    # 'rising', 'stable', 'declining'
    competition_level = Column(String(50))  # 'low', 'medium', 'high'
    
    # Recommendations
    recommendation_status = Column(String(50))  # 'recommended', 'neutral', 'avoid'
    usage_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<HashtagPerformanceTracking(hashtag={self.hashtag}, score={self.performance_score})>"


class InstagramGEOBenchmark(Base):
    """
    Benchmark data for industry comparisons
    """
    __tablename__ = 'instagram_geo_benchmarks'
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Benchmark categories
    business_type = Column(String(100), nullable=False)
    follower_range = Column(String(50))  # '1k-10k', '10k-100k', '100k+', etc.
    
    # Average scores
    average_overall_score = Column(Float)
    average_eeat_score = Column(Float)
    average_geo_score = Column(Float)
    average_visual_consistency = Column(Float)
    average_synergy_score = Column(Float)
    
    # Performance percentiles
    score_percentile_25 = Column(Float)
    score_percentile_50 = Column(Float)  # Median
    score_percentile_75 = Column(Float)
    score_percentile_90 = Column(Float)
    
    # Engagement benchmarks
    average_engagement_rate = Column(Float)
    average_reach_rate = Column(Float)
    average_save_rate = Column(Float)
    
    # Content characteristics
    optimal_post_frequency = Column(String(100))
    best_posting_times = Column(JSON)
    top_content_themes = Column(JSON)
    effective_hashtag_strategies = Column(JSON)
    
    # Sample size and confidence
    sample_size = Column(Integer)
    confidence_level = Column(Float)
    data_freshness_days = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<InstagramGEOBenchmark(business_type={self.business_type}, avg_score={self.average_overall_score})>"


# Database utility functions

def create_tables(engine):
    """
    Create all tables in the database
    
    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        Base.metadata.create_all(engine)
        logger.info("✅ All Instagram GEO analysis tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")
        return False


def drop_tables(engine):
    """
    Drop all tables from the database
    
    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        Base.metadata.drop_all(engine)
        logger.info("✅ All Instagram GEO analysis tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {str(e)}")
        return False


def get_table_info():
    """
    Get information about all tables in the schema
    
    Returns:
        Dictionary with table information
    """
    tables_info = {}
    
    for table_name, table in Base.metadata.tables.items():
        tables_info[table_name] = {
            'columns': [col.name for col in table.columns],
            'column_count': len(table.columns),
            'relationships': len(table.foreign_keys),
            'indexes': len(table.indexes)
        }
    
    return tables_info


def validate_schema():
    """
    Validate the database schema structure
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'total_tables': len(Base.metadata.tables),
        'tables': [],
        'total_columns': 0,
        'total_relationships': 0,
        'validation_passed': True,
        'issues': []
    }
    
    for table_name, table in Base.metadata.tables.items():
        table_info = {
            'name': table_name,
            'columns': len(table.columns),
            'foreign_keys': len([fk for fk in table.foreign_key_constraints]),
            'primary_keys': len(table.primary_key.columns)
        }
        
        validation_results['tables'].append(table_info)
        validation_results['total_columns'] += table_info['columns']
        validation_results['total_relationships'] += table_info['foreign_keys']
        
        # Validation checks
        if table_info['primary_keys'] == 0:
            validation_results['issues'].append(f"Table {table_name} has no primary key")
            validation_results['validation_passed'] = False
    
    return validation_results


# Export schema information
SCHEMA_INFO = {
    'version': '1.0.0',
    'description': 'Instagram GEO Analysis Database Schema',
    'tables': {
        'instagram_geo_analyses': 'Main analysis results and scores',
        'post_eeat_geo_scores': 'Individual post E-E-A-T and GEO scores',
        'geo_optimization_results': 'Content optimization recommendations',
        'visual_analysis_results': 'Visual consistency and quality analysis',
        'synergy_analysis_results': 'Post synergy and coherence analysis',
        'generated_instagram_content': 'Generated content and recommendations',
        'instagram_geo_reports': 'Generated analysis reports',
        'hashtag_performance_tracking': 'Hashtag usage and performance tracking',
        'instagram_geo_benchmarks': 'Industry benchmark data',
    },
    'key_features': [
        'Comprehensive E-E-A-T and GEO scoring',
        'Visual consistency tracking',
        'Post synergy analysis',
        'Content optimization storage',
        'Performance benchmarking',
        'Hashtag strategy tracking',
        'Generated content management'
    ]
}