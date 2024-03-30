import json

from setuptools import find_packages, setup

manifest = json.load(open("pinterest_cli/manifest.json", "r"))
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name=manifest["name"],
    version=manifest["version"],
    author=manifest["author"],
    description=manifest["description"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=manifest["license"],
    url=manifest["url"],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": [
            "manifest.json",
        ]
    },
    install_requires=["selenium>=4.9.0"],
    entry_points={
        "console_scripts": [
            "pinterest-cli = pinterest_cli.main:main",
        ],
    },
    python_rquires=">=3.10",
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Operating System :: Microsoft :: Windows",
    ],
)
