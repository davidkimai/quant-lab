"""Setup file for quant-lab-api package."""
from setuptools import setup, find_packages

setup(
    name="quant-lab-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "sqlalchemy>=2.0.25",
        "psycopg2-binary>=2.9.9",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.1.0",
        "aiofiles>=23.2.1",
        "requests",
    ],
)
