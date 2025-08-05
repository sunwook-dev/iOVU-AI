#!/usr/bin/env python3
"""
Modular Agents - Setup Script
브랜드 분석을 위한 모듈식 에이전트 시스템
"""

from setuptools import setup, find_packages
import os

# 현재 디렉토리 경로
here = os.path.abspath(os.path.dirname(__file__))

# README 읽기
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# 기본 requirements
install_requires = [
    # Database
    'pymysql>=1.0.0',
    'sqlalchemy>=1.4.0',
    
    # Web Crawling
    'requests>=2.28.0',
    'beautifulsoup4>=4.11.0',
    'selenium>=4.0.0',
    'playwright>=1.30.0',
    'trafilatura>=1.6.0',
    
    # Data Processing
    'pandas>=1.5.0',
    'numpy>=1.23.0',
    
    # AI/ML
    'openai>=1.0.0',
    'tiktoken>=0.5.0',
    
    # Text Processing
    'konlpy>=0.6.0',
    'nltk>=3.8.0',
    
    # Utils
    'python-dotenv>=0.19.0',
    'colorama>=0.4.6',
    'tqdm>=4.65.0',
    'schedule>=1.2.0',
    
    # Instagram
    'instagrapi>=1.16.0',
    
    # Logging
    'loguru>=0.7.0',
]

# 개발 dependencies
dev_requires = [
    'pytest>=7.0.0',
    'pytest-cov>=4.0.0',
    'black>=23.0.0',
    'flake8>=6.0.0',
    'isort>=5.12.0',
    'mypy>=1.0.0',
    'pre-commit>=3.0.0',
]

setup(
    name='modular-agents',
    version='2.0.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='브랜드 분석을 위한 모듈식 에이전트 시스템',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/modular_agents',
    packages=find_packages(exclude=['tests*', 'docs*', 'examples*']),
    python_requires='>=3.8',
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    keywords='brand analysis, web crawling, data processing, ai agents',
    entry_points={
        'console_scripts': [
            'modular-agents=modular_agents.cli:main',
            'ma-crawl=agent_02_web_crawler.main:main',
            'ma-clean=agent_04_text_cleaner.main:main',
            'ma-refine=agent_06_web_refiner.main:main',
            'ma-extract=agent_08_keyword_extractor.main:main',
            'ma-db-setup=database.quick_setup:main',
        ],
    },
    include_package_data=True,
    package_data={
        'modular_agents': [
            'database/setup_database.sql',
            'database/.env.example',
            'agent_*/.env.example',
            'README.md',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/modular_agents/issues',
        'Source': 'https://github.com/yourusername/modular_agents',
        'Documentation': 'https://modular-agents.readthedocs.io/',
    },
)