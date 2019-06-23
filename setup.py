#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name="singsparrow-ii",
    version="1.0.0",
    description="",
    url="https://github.com/evan-goode/singsparrow-ii",
    author="Evan Goode",
    author_email="mail@evangoo.de",
    license="GPLv3",
    install_requires=["toml"],
    packages=find_packages(),
    entry_points={"console_scripts": ["singsparrow-ii=singsparrow.singsparrow:main"]},
)
