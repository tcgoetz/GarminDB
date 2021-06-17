"""A database and database objects for storing health data from Garmin Connect."""

import re
import os
from setuptools import setup


def get_version(version_file):
    """Extract version fron the module source."""
    with open(version_file, 'r') as file:
        data = file.read()
        match = re.search(r'version_info = \((\d), (\d), (\d)\)', data, re.M)
        if match:
            return f'{match.group(1)}.{match.group(2)}.{match.group(3)}'


def get_long_description(readme_file):
    """Extract long description fron the module readme."""
    with open(readme_file, "r", encoding="utf-8") as file:
        return file.read()


module_name = 'garmindb'
module_version = get_version(module_name + os.sep + 'version_info.py')
module_long_description = get_long_description('README.md')

print(f"Building {module_name} {module_version}\n{module_long_description}")

setup(name=module_name, version=module_version, author='Tom Goetz',
      packages=[module_name, f'{module_name}.garmindb', f'{module_name}.fitbitdb', f'{module_name}.mshealthdb', f'{module_name}.summarydb'],
      scripts=['scripts/garmindb_cli.py', 'scripts/garmindb_graphs.py', 'scripts/garmindb_checkup.py', 'scripts/fitbit.py', 'scripts/mshealth.py'],
      description='Download data from Garmin Connect and store it in a SQLite db for analysis.',
      long_description=module_long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/tcgoetz/GarminDB",
      project_urls={"Bug Tracker": "https://github.com/tcgoetz/GarminDB/issues"},
      install_requires=open('requirements.txt').readlines(),
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          "Programming Language :: Python :: 3",
          "Operating System :: OS Independent"
      ],
      python_requires=">=3.0")
