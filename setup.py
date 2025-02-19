from setuptools import setup, find_packages

setup(
    name="leetcode-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "requests",
        "gql[all]"
    ],
    entry_points={
        "console_scripts": [
            "lc=src.main:app",
        ],
    }
)