from setuptools import find_packages, setup

setup(
    name="leetcode-cli",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "lc=src.main:main",
        ],
    },
)
