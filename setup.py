from setuptools import setup, find_packages

setup(
    name="chatbot_framework",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "openai",
        "httpx",
        "sse-starlette",
        "aiohttp",
        "sqlalchemy",
        "asyncpg",
        "alembic",
    ],
) 