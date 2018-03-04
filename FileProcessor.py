#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys, os, re, datetime


logger = logging.getLogger(__file__)


class FileProcessor():

    @classmethod
    def match_file(cls, input_file, file_regex):
        logger.info("Reading file: " + input_file)
        match = re.search(file_regex, input_file)
        if match:
            return [input_file]
        return []

    @classmethod
    def dir_to_files(cls, input_dir, file_regex, latest=False):
        logger.info("Reading directory: " + input_dir)
        file_names = []
        timestamp = datetime.datetime.now() - datetime.timedelta(1)
        for file in os.listdir(input_dir):
            match = re.search(file_regex, file)
            file_with_path = input_dir + "/" + file
            if match and (not latest or datetime.datetime.fromtimestamp(os.stat(file_with_path).st_ctime) > timestamp):
                file_names.append(file_with_path)
        return file_names
