#!/usr/bin/env python

#
# copyright Tom Goetz
#

import json, logging
import dateutil.parser

import FileProcessor


logger = logging.getLogger(__file__)


class JsonFileProcessor(object):

    def __init__(self, input_file, input_dir, file_regex, latest, debug):
        self.debug = debug
        logger.info("Debug: %s" % str(debug))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, file_regex)
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, file_regex, latest)

    def file_count(self):
        return len(self.file_names)

    @classmethod
    def parse_file(cls, filename, conversions):
        def parser(entry):
            for (conversion_key, conversion_func) in conversions.iteritems():
                entry_value = entry.get(conversion_key, None)
                if entry_value is not None:
                    entry[conversion_key] = conversion_func(entry_value)
            return entry
        return json.load(open(filename), object_hook=parser)

    def process_file(self, file_name):
        pass

    def process_files(self):
        logger.info("Processing %d json files", self.file_count())
        for file_name in self.file_names:
            try:
                self.process_file(file_name)
            except Exception as e:
                logger.error("Failed to parse %s: %s", file_name, str(e))
        logger.info("DB updated with %d entries.", self.file_count())
