import os

from setuptools import find_packages
from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(__file__, os.pardir)))

setup(
    packages=find_packages(),
    include_package_data=True,
)
