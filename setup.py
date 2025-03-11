from setuptools import setup, find_packages

setup(
    name="diagram_generator",
    version="0.1.0",
    description="A tool for generating diagrams using LLM",
    author="",
    author_email="",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "langchain>=0.0.350",
        "langgraph>=0.0.20",
        "sqlalchemy>=2.0.23",
        "pydantic>=2.5.0",
        "requests>=2.31.0",
        "requests-cache>=1.1.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.25.0",
        "langchain-community>=0.0.16",
        "langchain-core>=0.1.0",
        "langchain-ollama>=0.0.1",
        "faiss-cpu>=1.7.4",
        "numpy>=1.26.0",
        "aiohttp>=3.9.0",
        "jinja2>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "diagram-generator-backend=diagram_generator.backend.main:run_server",
            "diagram-generator=diagram_generator.cli:main",
        ],
    },
)
