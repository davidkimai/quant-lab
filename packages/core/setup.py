"""Setup file for quant-lab-core package."""
from setuptools import setup, find_packages

setup(
    name="quant-lab-core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "pydantic>=2.6.0",
        "yfinance>=0.2.36",
        "python-dateutil>=2.8.2",
    ],
)
