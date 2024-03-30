import json

from setuptools import find_packages, setup

manifest = json.load(open("pinterest_cli/manifest.json", "r"))

setup(
    name=manifest["name"],
    version=manifest["version"],
    author=manifest["author"],
    description=manifest["description"],
    url=manifest["url"],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": [
            "manifest.json",
        ]
    },
    install_requires=["selenium"],
    entry_points={
        "console_scripts": [
            "pinterest-cli = pinterest_cli.main:main",
        ],
    },
)
