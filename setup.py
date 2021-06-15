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

setup(name=module_name, version=module_version, author='Tom Goetz',
      packages=[module_name, f'{module_name}.garmindb', f'{module_name}.fitbitdb', f'{module_name}.mshealthdb', f'{module_name}.summarydb'],
      scripts=['scripts/garmin.py', 'scripts/garmin_graphs.py', 'scripts/garmin_checkup.py', 'scripts/fitbit.py', 'scripts/mshealth.py'],
      license=open('LICENSE').read(),
      description='Download data from Garmin Connect and store it in a SQLite db for analysis.',
      long_description=get_long_description('README.md'),
      url="https://github.com/tcgoetz/GarminDB",
      project_urls={"Bug Tracker": "https://github.com/tcgoetz/GarminDB/issues"},
      install_requires=open('requirements.txt').readlines(),
      python_requires=">=3.0")
