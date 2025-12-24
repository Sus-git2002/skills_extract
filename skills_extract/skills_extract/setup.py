from setuptools import find_packages, setup

setup(
    name='skills_extraction_pipeline',
    packages=find_packages(),
    version='1.0.0',
    description='A production-grade pipeline for extracting skills from job descriptions',
    author='Your Name',
    author_email='your.email@example.com',
    license='MIT',
    python_requires='>=3.8',
    install_requires=[
        'pandas>=2.0.0',
        'pyyaml>=6.0',
        'chardet>=5.0.0',
        'openpyxl>=3.1.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'flake8>=6.0.0',
            'black>=23.0.0',
            'isort>=5.12.0',
        ],
        'nlp': [
            'spacy>=3.5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'extract-skills=run_pipeline:main',
        ],
    },
)
