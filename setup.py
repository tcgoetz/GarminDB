"""A database and database objects for storing health data from Garmin Connect."""

import re
import os
from setuptools import setup


def get_version(version_file):
    """Extract version fron the module source."""
    print(f"Loading version from {version_file} in {os.getcwd()}")
    with open(version_file, 'r') as file:
        data = file.read()
        match = re.search(r'version_info = \((\d), (\d), (\d)\)', data, re.M)
        if match:
            return f'{match.group(1)}.{match.group(2)}.{match.group(3)}'


def get_long_description(ld_file):
    """Extract long description fron the module readme."""
    print(f"Loading long description from {ld_file} in {os.getcwd()}")
    with open(ld_file, "r", encoding="utf-8") as file:
        return file.read()


def get_requirements(requirements_file):
    """Extract long requirements fron the module requirements.txt."""
    print(f"Loading requirements from {requirements_file} in {os.getcwd()}")
    with open(requirements_file, "r", encoding="utf-8") as file:
        return file.readlines()


module_name = 'garmindb'
module_version = get_version(module_name + os.sep + 'version_info.py')
module_long_description = get_long_description('README.md')
install_requires = get_requirements('requirements.txt')

print(f"Building {module_name} {module_version}")


setup(name=module_name, version=module_version, author='Tom Goetz',
      packages=[module_name, f'{module_name}.garmindb', f'{module_name}.fitbitdb', f'{module_name}.mshealthdb', f'{module_name}.summarydb'],
      scripts=['scripts/garmindb_cli.py', 'scripts/garmindb_checkup.py', 'scripts/garmindb_bug_report.py', 'scripts/fitbit.py', 'scripts/mshealth.py'],
      description='Download data from Garmin Connect and store it in a SQLite db for analysis.',
      long_description=module_long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/tcgoetz/GarminDB",
      project_urls={"Bug Tracker": "https://github.com/tcgoetz/GarminDB/issues"},
      install_requires=install_requires,
      include_package_data=True,
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          "Programming Language :: Python :: 3",
          "Operating System :: OS Independent"
      ],
      python_requires=">=3.0")
