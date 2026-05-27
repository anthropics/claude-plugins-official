#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  ARKHE WORLD MODEL — Setup Package                              ║
# ║  Substrato 890                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arkhe-world-model",
    version="890.0.0",
    author="ARKHE Cathedral",
    author_email="arkhe@cathedral.ai",
    description="Embryonic World Model for ARKHE-OS (Substrate 890)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arkhe-cathedral/world-model",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "torch>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
    ],
    extras_require={
        "llm": ["llama-cpp-python>=0.2.0"],
        "sim": ["brax>=0.9.0", "jax>=0.4.0", "jaxlib>=0.4.0"],
        "rl": ["gymnasium>=0.28.0", "stable-baselines3>=2.0.0"],
        "dev": ["pytest>=7.0", "black>=23.0", "mypy>=1.0"],
    },
    entry_points={
        "console_scripts": [
            "arkhe-train=train:main",
            "arkhe-demo=demo:main",
        ],
    },
)
