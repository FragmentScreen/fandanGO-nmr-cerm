from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Load requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='fandanGO-nmr-cerm',
    version='0.1.0',
    description='nmr-cerm plugin of the FandanGO application',
    long_description=long_description,
    author='CNB-CSIC, Irene Sanchez, Instruct-ERIC, Lui Holliday, Marcus Povey, Yvonne De Jong-Leung, CERM, Andrea Giachetti',
    author_email='isanchez@cnb.csic.es, lui.holliday@instruct-eric.org, marcus@instruct-eric.org, yvonne.de.jong-leung@instruct-eric.org, andrea.giachetti@protonmail.com',
    packages=find_packages(),
    install_requires=[requirements],
    entry_points={
        'fandango.plugin': 'fandanGO-nmr-cerm = nmrcerm'
    },
)