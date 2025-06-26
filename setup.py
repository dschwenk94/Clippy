#!/usr/bin/env python
"""
Clippy - AI-Powered YouTube Shorts Generator
Setup script for package installation
"""

from setuptools import setup, find_packages
import os

# Read the README file for the long description
def read_long_description():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements_webapp.txt
def read_requirements():
    with open("requirements_webapp.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="clippy-viral-generator",
    version="2.0.0",
    author="DS",
    author_email="schwenkedavis@gmail.com",
    description="AI-powered YouTube Shorts generator with auto-peak detection and viral captions",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/dschwenk94/Clippy",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "clippy=app:main",
            "clippy-server=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.html", "static/**/*", "configs/*.json"],
    },
    project_urls={
        "Bug Reports": "https://github.com/dschwenk94/Clippy/issues",
        "Source": "https://github.com/dschwenk94/Clippy",
        "Documentation": "https://github.com/dschwenk94/Clippy/tree/main/docs",
    },
    keywords="youtube shorts video ai caption viral tiktok",
)
