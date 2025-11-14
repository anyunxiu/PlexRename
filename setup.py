from setuptools import setup, find_packages
from pathlib import Path

# 读取项目版本和描述
try:
    with open(Path(__file__).parent / "README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Plex文件重命名工具，支持硬链接、元数据获取和Web UI管理"

setup(
    name="plexrename",
    version="1.0.0",
    description="Plex文件重命名工具，支持硬链接、元数据获取和Web UI管理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="",
    author_email="",
    url="",
    packages=find_packages(),
    package_data={
        'app.web': ['templates/*', 'static/css/*', 'static/js/*'],
        'app': ['*.py', 'config/*.py', 'core/*.py', 'metadata/*.py', 'monitor/*.py', 'web/*.py']
    },
    include_package_data=True,
    install_requires=[
        'flask>=2.0.0',
        'flask-socketio>=5.0.0',
        'requests>=2.25.0',
        'watchdog>=2.1.0',
        'python-dotenv>=0.19.0',
        'pydantic>=1.8.0',
        'eventlet>=0.33.0'
    ],
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'black>=21.0.0',
            'flake8>=4.0.0'
        ]
    },
    entry_points={
        'console_scripts': [
            'plexrename = app.main:main'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    python_requires='>=3.8',
    keywords='plex, rename, hardlink, metadata, tmdb, douban'
)