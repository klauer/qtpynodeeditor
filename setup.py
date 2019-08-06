import pathlib
import sys
from os import path

from setuptools import find_packages, setup

import versioneer

min_version = (3, 6)

if sys.version_info < min_version:
    error = """
qtpynodeeditor does not support Python {0}.{1}.
Python {2}.{3} and above is required. Check your Python version like so:

python3 --version

This may be due to an out-of-date pip. Make sure you have pip >= 9.0.1.
Upgrade pip like so:

pip install --upgrade pip
""".format(*sys.version_info[:2], *min_version)
    sys.exit(error)


here = pathlib.Path(__file__).parent.absolute()

with open(here / 'README.rst', encoding='utf-8') as readme_file:
    readme = readme_file.read()

with open(here / 'requirements.txt', 'rt') as requirements_file:
    # Parse requirements.txt, ignoring any commented-out lines.
    requirements = [line for line in requirements_file.read().splitlines()
                    if not line.startswith('#')]


setup(
    name='qtpynodeeditor',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    license='BSD',
    author='Ken Lauer',
    packages=find_packages(exclude=['docs', 'tests']),
    description='Python Qt node editor',
    long_description=readme,
    url='https://github.com/klauer/qtpynodeeditor',
    entry_points={
        'console_scripts': [
            # 'some.module:some_function',
        ],
    },
    include_package_data=True,
    package_data={
        'qtpynodeeditor': [
            # When adding files here, remember to update MANIFEST.in as well,
            # or else they will not be included in the distribution on PyPI!
            'qtpynodeeditor/DefaultStyle.json',
        ]
    },
    install_requires=requirements,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
