# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))

def read(fname: str) -> str:
    return open(path.join(path.dirname(__file__), fname)).read()

def find_version() -> str:
    version_file = read("geomloss/version.py")
    version_re = r"__version__ = \"(?P<version>.+)\""
    version_raw = re.match(version_re, version_file)
    if version_raw is None:
        return "0.0.1"

    version = version_raw.group("version")
    return version

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="geomloss",
    version=find_version(),
    description="Geometric loss functions between point clouds, images and volumes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jean Feydy",
    author_email="jean.feydy@inria.fr",
    python_requires=">=3",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="kernels optimal transport measure loss geometry",
    packages=["geomloss"],
    package_data={"geomloss": []},
    scripts=[],
    url="",
    license="LICENSE.txt",
    install_requires=[
        "numpy",
    ],
    extras_require={
        "full": [
            "pykeops",
        ],
    },
)
