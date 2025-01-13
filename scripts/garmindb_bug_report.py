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
import os
import os.path
import argparse


logging.basicConfig(filename='bugreport.log', filemode='w', level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


def main(argv):
    """Run a data checkup of the user's choice."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Directory where Garmindb scripts were run", required=True)
    args = parser.parse_args()

    bug_report_txt = args.dir + os.sep + 'bugreport.txt'

    with open(bug_report_txt, 'w') as report:
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
            requirements_file_path = args.dir + os.sep + requirements_file
            report.write(f'\nrequirements {requirements_file_path}\n\n')
            output = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze', requirements_file_path])
            report.write(output.decode())

    with zipfile.ZipFile(args.dir +  os.sep + 'bugreport.zip', 'w') as zip:
        zip.write(bug_report_txt)
        garmindb_log = args.dir + os.sep + 'garmindb.log'
        if os.path.isfile(garmindb_log):
            zip.write(garmindb_log)


if __name__ == "__main__":
    main(sys.argv[1:])
