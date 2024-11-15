from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="amta",
    version="1.0.0",
    author="Premshay Hermon",
    author_email="atlomy@mail.huji.ac.il",
    description="A production-ready tool for analyzing ancient medical texts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Atlogit/atlomy_chat",
    packages=find_packages(include=["app.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Academic Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps",
        "Topic :: Text Processing :: Linguistic Processing",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas==2.2.3",
        "numpy==1.26.4",
        "fastapi==0.111.1",
        "uvicorn==0.22.0",
        "sse-starlette==2.1.3",
        "SQLAlchemy==2.0.36",
        "alembic==1.13.3",
        "asyncpg==0.30.0",
        "boto3==1.35.49",
        "typing-extensions==4.12.2",
        "pydantic==2.9.2",
        "pydantic-settings==2.6.0",
        "regex==2024.9.11",
        "httpx==0.27.2",
        "python-dotenv==1.0.1",
        "asyncio==3.4.3",
        "loguru==0.7.2",
    ],
    extras_require={
        'dev': [
            "pytest==8.3.3",
            "pytest-asyncio==0.24.0",
            "psutil==6.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "amta=app.run_server:main",
        ],
    },
    keywords="medical-text research ancient-texts production",
)
