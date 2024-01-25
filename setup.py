#!/usr/bin/env python
# encoding: utf-8
"""
setup.py

Created by <frgray@gmail.com>
"""

from setuptools import setup, find_packages
import os

exec(
    compile(
        open(os.path.join(os.path.dirname(__file__), "version.py"), "rb").read(),
        os.path.join(os.path.dirname(__file__), "version.py"),
        "exec",
    )
)

setup(
    name="frgray-network",
    description="",
    version=".".join(map(str, VERSION)),
    packages=find_packages(),
    author="Francisco Gray",
    author_email="frgray@gmail.com",
    install_requires=["pulumi>=3.0.0,<4.0.0", "pulumi-aws>=6.0.2,<7.0.0"],
)
