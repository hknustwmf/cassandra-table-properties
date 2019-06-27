import os
import setuptools

long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name="cassandra-table-properties",
    version="1.0.0",
    author="Holger Knust",
    author_email="hknust@wikimedia.org",
    description="Cassandra table and keyspace configuration tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hknustwmf/cassandra-table-properties",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX",
    ],
)