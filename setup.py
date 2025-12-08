"""
Setup script for NutriSénégal package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="nutrisenegal",
    version="1.0.0",
    author="Votre Nom",
    author_email="votre.email@example.com",
    description="Système de recommandation alimentaire intelligent basé sur ML et règles métier",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NandoDP/food-recommandation-system",
    packages=find_packages(exclude=["tests", "notebooks", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "docs": [
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nutrisenegal-api=api.main:main",
            "nutrisenegal-bot=telegram_bot.bot:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "nutrition",
        "health",
        "recommendation-system",
        "machine-learning",
        "data-science",
        "nlp",
        "fastapi",
        "telegram-bot",
        "diabetes",
        "hypertension",
        "food-analysis",
    ],
    project_urls={
        "Bug Reports": "https://github.com/NandoDP/food-recommandation-system/issues",
        "Source": "https://github.com/NandoDP/food-recommandation-system",
        "Documentation": "https://github.com/NandoDP/food-recommandation-system/blob/main/README.md",
    },
)
