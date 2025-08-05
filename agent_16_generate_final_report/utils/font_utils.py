"""
Font utilities for matplotlib
"""

import matplotlib.pyplot as plt

def setup_matplotlib_fonts():
    """폰트 설정"""
    try:
        import platform as pf
        if pf.system() == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        elif pf.system() == 'Darwin':
            plt.rc('font', family='AppleGothic')
        else:
            plt.rc('font', family='NanumGothic')
    except Exception as e:
        print(f"폰트 설정 중 오류 발생: {e}. 차트의 한글이 깨질 수 있습니다.")

    plt.style.use('seaborn-v0_8-poster')
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.dpi'] = 150
