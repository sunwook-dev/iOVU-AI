"""
Platform comparison charts
"""

import matplotlib.pyplot as plt
import numpy as np

def create_platform_comparison_charts(df_all, output_folder, brand_name):
    """플랫폼별 비교 차트 생성"""
    
    # 차트 데이터 콘솔 출력
    colors = ['#4285F4', '#EA4335', '#34A853', '#F9AB00', '#A142F4', '#00B7C3']
    eeat_labels = ["Experience", "Expertise", "Authoritativeness", "Trustworthiness"]
    eeat_keys = ["experience_avg", "expertise_avg", "authoritativeness_avg", "trustworthiness_avg"]
    geo_labels = ["명료성", "구조성", "맥락성", "일치성", "적시성", "독창성"]
    geo_keys = ["clarity_avg", "structure_avg", "context_avg", "alignment_avg", "timeliness_avg", "originality_avg"]
    
    platforms = df_all['platform'].unique()
    
    print("\n" + "="*60)
    print("📊 E-E-A-T 차트 데이터")
    print("="*60)
    for i, platform in enumerate(platforms):
        sub = df_all[df_all['platform'] == platform].head(10)
        stats = sub[eeat_keys].agg(['max', 'mean', 'min']).round(2)
        print(f"\n🔹 {platform}:")
        print(f"   최대값: {dict(zip(eeat_labels, stats.loc['max']))}")
        print(f"   평균값: {dict(zip(eeat_labels, stats.loc['mean']))}")
        print(f"   최소값: {dict(zip(eeat_labels, stats.loc['min']))}")
    
    print("\n" + "="*60)
    print("📊 GEO 레이더 차트 데이터")
    print("="*60)
    for i, platform in enumerate(platforms):
        sub = df_all[df_all['platform'] == platform].head(10)
        geo_stats = sub[geo_keys].mean().round(2)
        print(f"\n🔹 {platform}:")
        print(f"   GEO 평균: {dict(zip(geo_labels, geo_stats))}")
        print(f"   데이터 개수: {len(sub)}")
    print("="*60)

    # 플랫폼별 Overall Score
    plat_stats = df_all.groupby('platform')[['overall_score']].mean().round(2)
    fig, ax = plt.subplots(figsize=(12, 8))
    data_to_plot = plat_stats['overall_score'].sort_values()
    colors_bar = plt.cm.summer(np.linspace(0.4, 1, len(data_to_plot)))
    
    bars = ax.barh(data_to_plot.index, data_to_plot, color=colors_bar)
    ax.bar_label(bars, fmt='%.1f', padding=-40, color='white', fontsize=16, weight='bold')
    ax.set_title('플랫폼별 Overall Score 평균', fontsize=20, pad=20)
    ax.set_xlabel('평균 점수', fontsize=14)
    ax.tick_params(axis='y', labelsize=14)
    ax.set_xlim(0, 100)
    ax.xaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(f'{output_folder}/{brand_name}_platform_score_chart.png')
    plt.close()
    print(f"차트 생성: {brand_name}_platform_score_chart.png")

    # Synergy 점수 통계
    stat_labels = ['최대값', '최소값', '평균값']
    stat_keys = ['max', 'min', 'mean']
    
    synergy_data = []
    for platform in platforms:
        sub = df_all[df_all['platform'] == platform].head(10)
        stats = sub['synergy_avg'].agg(stat_keys).round(2)
        vals = [stats[k] for k in stat_keys]
        synergy_data.append(vals)
        
    synergy_data = np.array(synergy_data)
    n_platforms = len(platforms)
    n_stats = len(stat_labels)
    x = np.arange(n_stats)
    bar_width = 0.8 / n_platforms
    
    fig, ax = plt.subplots(figsize=(12, 8))
    for i, (platform, vals) in enumerate(zip(platforms, synergy_data)):
        bar_position = x + i * bar_width - (bar_width * (n_platforms - 1) / 2)
        bars = ax.bar(bar_position, vals, width=bar_width, label=platform, color=colors[i % len(colors)])
        ax.bar_label(bars, fmt='%.2f', padding=3, fontsize=11)
            
    ax.set_xticks(x)
    ax.set_xticklabels(stat_labels, fontsize=15)
    ax.set_title('플랫폼별 Synergy 점수 통계 (최대/최소/평균)', fontsize=20, pad=20)
    ax.set_ylabel('Synergy 점수', fontsize=15)
    ax.set_ylim(0, 115)
    ax.get_yaxis().set_ticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.legend(fontsize=14)
    
    plt.tight_layout()
    plt.savefig(f'{output_folder}/{brand_name}_platform_synergy_chart.png')
    plt.close()
    print(f"차트 생성: {brand_name}_platform_synergy_chart.png")
