from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="trafapy",
    version="0.1.0",
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "pandas>=1.0.0",
        "numpy>=1.19.0",
    ],
    author="Emanuel Raptis",
    description="A Python wrapper for the Trafikanalys API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xemarap/trafapy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="trafikanalys, api, statistics, sweden, transport, traffic",
)