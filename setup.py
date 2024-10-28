from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="atlomy_chat",
    version="0.1.0",
    author="Premshay Hermon",
    author_email="atlomy@mail.huji.ac.il",
    description="A tool for analyzing and querying ancient medical texts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Atlogit/atlomy_chat",
    packages=find_packages(include=["src.*", "app.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "spacy",
        "spacy-transformers",
        "langchain",
        "langchain-aws",
        "typing-extensions",
        "pathlib",
        "boto3",
        "botocore",
        "pytest",
        "jupyter",
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "redis",
        "aioredis",
        "asyncpg",
        "pydantic",
        "pydantic-settings",
    ],
    entry_points={
        "console_scripts": [
            "atlomy_chat=atlomy_chat.cli:main",
        ],
    },
)
