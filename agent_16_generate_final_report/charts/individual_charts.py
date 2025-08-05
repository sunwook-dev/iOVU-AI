"""
Individual platform charts (Instagram, Blog)
"""

import matplotlib.pyplot as plt
import numpy as np

def create_individual_charts(df_insta, df_blog, output_folder, brand_name):
    """개별 플랫폼 차트 생성 (Instagram, Blog 별도)"""
    
    # Instagram 개별 차트
    if df_insta is not None and not df_insta.empty:
        # Instagram E-E-A-T
        fig, ax = plt.subplots(figsize=(12, 7))
        colors = ['#4285F4', '#EA4335']
        eeat_labels = ["Experience", "Expertise", "Authoritativeness", "Trustworthiness"]
        eeat_keys = ["experience_avg", "expertise_avg", "authoritativeness_avg", "trustworthiness_avg"]
        
        for i, platform in enumerate(df_insta['platform'].unique()):
            sub = df_insta[df_insta['platform'] == platform].head(10)
            stats = sub[eeat_keys].agg(['max', 'mean', 'min']).round(2)
            
            ax.plot(eeat_labels, stats.loc['max'], marker='o', linestyle=':', label=f'{platform} 최대', color=colors[i%len(colors)], alpha=0.5)
            ax.plot(eeat_labels, stats.loc['mean'], marker='s', linestyle='-', label=f'{platform} 평균', linewidth=3, color=colors[i%len(colors)], alpha=0.9)
            ax.plot(eeat_labels, stats.loc['min'], marker='x', linestyle=':', label=f'{platform} 최소', color=colors[i%len(colors)], alpha=0.5)
        
        ax.set_title('Instagram E-E-A-T 세부항목 점수 분포', fontsize=20, pad=20)
        ax.set_ylabel('점수', fontsize=14)
        ax.legend(fontsize=12)
        ax.grid(True, axis='y', linestyle='--', alpha=0.6)
        ax.set_ylim(0, 105)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{brand_name}_insta_eeat_line_chart.png')
        plt.close()
        print(f"차트 생성: {brand_name}_insta_eeat_line_chart.png")

        # Instagram GEO 레이더
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        geo_labels = ["명료성", "구조성", "맥락성", "일치성", "적시성", "독창성"]
        geo_keys = ["clarity_avg", "structure_avg", "context_avg", "alignment_avg", "timeliness_avg", "originality_avg"]
        angles = np.linspace(0, 2 * np.pi, len(geo_labels), endpoint=False).tolist()
        
        for i, platform in enumerate(df_insta['platform'].unique()):
            sub = df_insta[df_insta['platform'] == platform].head(10)
            geo_stats = sub[geo_keys].mean().tolist()
            geo_stats += geo_stats[:1]
            angs = angles + angles[:1]
            
            ax.plot(angs, geo_stats, 'o-', linewidth=3, color=colors[i%len(colors)], label=platform)
            ax.fill(angs, geo_stats, color=colors[i%len(colors)], alpha=0.15)
            
        ax.set_thetagrids(np.degrees(angles), geo_labels, fontsize=14)
        ax.set_title('Instagram GEO 세부항목 평균 점수', fontsize=20, y=1.1, pad=20)
        ax.set_rlim(0, 100)
        ax.set_rlabel_position(22.5)
        ax.tick_params(axis='y', labelsize=10)
        ax.legend(fontsize=13, loc='upper right', bbox_to_anchor=(1.2, 1.1))
        
        plt.savefig(f'{output_folder}/{brand_name}_insta_geo_radar_chart.png', bbox_inches='tight')
        plt.close()
        print(f"차트 생성: {brand_name}_insta_geo_radar_chart.png")

    # Blog 개별 차트
    if df_blog is not None and not df_blog.empty:
        # Blog E-E-A-T
        fig, ax = plt.subplots(figsize=(12, 7))
        blog_colors = ['#34A853', '#F9AB00']
        
        for i, platform in enumerate(df_blog['platform'].unique()):
            sub = df_blog[df_blog['platform'] == platform].head(10)
            stats = sub[eeat_keys].agg(['max', 'mean', 'min']).round(2)
            
            ax.plot(eeat_labels, stats.loc['max'], marker='o', linestyle=':', label=f'{platform} 최대', color=blog_colors[i%len(blog_colors)], alpha=0.5)
            ax.plot(eeat_labels, stats.loc['mean'], marker='s', linestyle='-', label=f'{platform} 평균', linewidth=3, color=blog_colors[i%len(blog_colors)], alpha=0.9)
            ax.plot(eeat_labels, stats.loc['min'], marker='x', linestyle=':', label=f'{platform} 최소', color=blog_colors[i%len(blog_colors)], alpha=0.5)
        
        ax.set_title('Blog E-E-A-T 세부항목 점수 분포', fontsize=20, pad=20)
        ax.set_ylabel('점수', fontsize=14)
        ax.legend(fontsize=12)
        ax.grid(True, axis='y', linestyle='--', alpha=0.6)
        ax.set_ylim(0, 105)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{brand_name}_blog_eeat_line_chart.png')
        plt.close()
        print(f"차트 생성: {brand_name}_blog_eeat_line_chart.png")

        # Blog GEO 레이더
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        for i, platform in enumerate(df_blog['platform'].unique()):
            sub = df_blog[df_blog['platform'] == platform].head(10)
            geo_stats = sub[geo_keys].mean().tolist()
            geo_stats += geo_stats[:1]
            angs = angles + angles[:1]
            
            ax.plot(angs, geo_stats, 'o-', linewidth=3, color=blog_colors[i%len(blog_colors)], label=platform)
            ax.fill(angs, geo_stats, color=blog_colors[i%len(blog_colors)], alpha=0.15)
            
        ax.set_thetagrids(np.degrees(angles), geo_labels, fontsize=14)
        ax.set_title('Blog GEO 세부항목 평균 점수', fontsize=20, y=1.1, pad=20)
        ax.set_rlim(0, 100)
        ax.set_rlabel_position(22.5)
        ax.tick_params(axis='y', labelsize=10)
        ax.legend(fontsize=13, loc='upper right', bbox_to_anchor=(1.2, 1.1))
        
        plt.savefig(f'{output_folder}/{brand_name}_blog_geo_radar_chart.png', bbox_inches='tight')
        plt.close()
        print(f"차트 생성: {brand_name}_blog_geo_radar_chart.png")
