"""
Website analysis charts
"""

import matplotlib.pyplot as plt
import numpy as np

def create_website_charts(df_website, output_folder, brand_name):
    """웹사이트 분석 차트 생성"""
    if df_website is None or df_website.empty:
        print("웹사이트 데이터가 없어 차트를 생성하지 않습니다.")
        return
    
    print("\n" + "="*60)
    print("🌐 웹사이트 차트 데이터 디버깅")
    print("="*60)
    print("📊 df_website 구조:")
    print(f"   - Shape: {df_website.shape}")
    print(f"   - Columns: {list(df_website.columns)}")
    print(f"   - First row data:")
    for col in df_website.columns:
        print(f"     {col}: {df_website.iloc[0][col]}")
    
    # GEO 레이더 차트
    geo_keys = ['clarity', 'structure', 'context', 'alignment', 'timeliness', 'originality']
    geo_labels = ['명료성', '구조성', '맥락성', '일치성', '적시성', '독창성']
    
    print(f"\n📈 GEO 차트 생성 시작...")
    print(f"   - geo_keys: {geo_keys}")
    print(f"   - geo_labels: {geo_labels}")
    
    # 데이터 추출 및 오류 처리
    geo_stats = []
    for i, key in enumerate(geo_keys):
        try:
            if key in df_website.columns:
                value = float(df_website.iloc[0][key])
                geo_stats.append(value)
                print(f"   - {geo_labels[i]} ({key}): {value}")
            else:
                print(f"   ❌ 컬럼 '{key}' 찾을 수 없음 - 기본값 0 사용")
                geo_stats.append(0.0)
        except (ValueError, TypeError) as e:
            print(f"   ❌ {geo_labels[i]} ({key}) 변환 오류: {e} - 기본값 0 사용")
            geo_stats.append(0.0)
    
    print(f"   - 최종 geo_stats: {geo_stats}")
    
    angles = np.linspace(0, 2 * np.pi, len(geo_labels), endpoint=False).tolist()
    geo_stats += geo_stats[:1]
    angs = angles + angles[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    ax.plot(angs, geo_stats, 'o-', linewidth=3, color='mediumseagreen', label='점수')
    ax.fill(angs, geo_stats, color='mediumseagreen', alpha=0.2)
    ax.set_thetagrids(np.degrees(angles), geo_labels, fontsize=14)
    ax.set_title('웹사이트 GEO 세부항목 점수', fontsize=20, y=1.1, pad=20)
    ax.set_rlim(0, 100)
    ax.set_rlabel_position(22.5)
    ax.tick_params(axis='y', labelsize=10)
    
    plt.tight_layout()
    plt.savefig(f'{output_folder}/{brand_name}_website_geo_radar_chart.png')
    plt.close()
    print(f"✅ 차트 생성: {brand_name}_website_geo_radar_chart.png")

    # SEO/GEO Before & After 비교
    print(f"\n📊 SEO/GEO Before & After 차트 생성...")
    labels = ['SEO 점수', 'GEO 점수']
    
    # Before 점수 추출 및 오류 처리
    before_scores = []
    after_scores = []
    
    score_keys = [
        ('original_seo_score', 'after_seo_score'),
        ('original_geo_score', 'after_geo_score')
    ]
    
    for i, (before_key, after_key) in enumerate(score_keys):
        try:
            if before_key in df_website.columns:
                before_val = float(df_website.iloc[0][before_key])
                before_scores.append(before_val)
                print(f"   - {labels[i]} Before ({before_key}): {before_val}")
            else:
                print(f"   ❌ 컬럼 '{before_key}' 찾을 수 없음 - 기본값 0 사용")
                before_scores.append(0.0)
                
            if after_key in df_website.columns:
                after_val = float(df_website.iloc[0][after_key])
                after_scores.append(after_val)
                print(f"   - {labels[i]} After ({after_key}): {after_val}")
            else:
                print(f"   ❌ 컬럼 '{after_key}' 찾을 수 없음 - 기본값 0 사용")
                after_scores.append(0.0)
        except (ValueError, TypeError) as e:
            print(f"   ❌ {labels[i]} 점수 변환 오류: {e} - 기본값 0 사용")
            before_scores.append(0.0)
            after_scores.append(0.0)
    
    print(f"   - before_scores: {before_scores}")
    print(f"   - after_scores: {after_scores}")
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 7))
    rects1 = ax.bar(x - width/2, before_scores, width, label='Before', color='silver')
    rects2 = ax.bar(x + width/2, after_scores, width, label='After (예상)', color='mediumseagreen')
    
    ax.set_title('웹사이트 최적화 Before & After 점수 비교', fontsize=18, pad=20)
    ax.set_ylabel('점수')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 120)
    ax.legend()
    ax.bar_label(rects1, padding=3)
    ax.bar_label(rects2, padding=3, weight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_folder}/{brand_name}_website_optimization_chart.png')
    plt.close()
    print(f"차트 생성: {brand_name}_website_optimization_chart.png")
