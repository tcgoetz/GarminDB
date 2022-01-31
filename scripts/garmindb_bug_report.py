#!/usr/bin/env python3

"""Generate a bug report text file to be included with a bug report."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import platform
import sysconfig
import logging
import subprocess
import zipfile


logging.basicConfig(filename='bugreport.log', filemode='w', level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


with open('bugreport.txt', 'w') as report:
    report.write(f"sys.version: {sys.version}\n")
    report.write(f"sys.platform: {sys.platform}\n")
    report.write(f"platform.system(): {platform.system()}\n")
    report.write(f"sysconfig.get_platform(): {sysconfig.get_platform()}\n")
    report.write(f"platform.machine(): {platform.machine()}\n")
    report.write(f"platform.architecture(): {platform.architecture()}\n\n")

    output = subprocess.check_output([sys.executable, '-m', 'pip', 'show', 'garmindb'])
    report.write(output.decode())

    requirements_files = ["requirements.txt", 'Fit/requirements.txt' 'utilities/requirements.txt', 'tcx/requirements.txt']

    for requirements_file in requirements_files:
        report.write(f'\nrequirements {requirements_file}\n\n')
        output = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze', requirements_file])
        report.write(output.decode())

with zipfile.ZipFile('bugreport.zip', 'w') as zip:
    zip.write('bugreport.txt')
    zip.write('garmindb.log')
