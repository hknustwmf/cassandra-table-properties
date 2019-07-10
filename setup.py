#! /usr/bin/env python3
""" Setup file
"""
import os
import setuptools

LONG_DESC = ""
if os.path.exists("README.md"):
    with open("README.md", "r") as fh:
        LONG_DESC = fh.read()

setuptools.setup(
    name="cassandra-table-properties",
    version="0.3.0",
    author="Holger Knust",
    author_email="hknust@wikimedia.org",
    description="Cassandra table and keyspace configuration tool.",
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",
    url="https://github.com/hknustwmf/cassandra-table-properties",
    packages=setuptools.find_packages(),
    install_requires=[
        "cassandra-driver",
        "PyYAML"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX",
    ],
    entry_points={
        'console_scripts': [
            'table-properties = table_properties.cli:main'
        ],
    }
)