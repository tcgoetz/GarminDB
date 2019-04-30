#!/usr/bin/env python

#
# copyright Tom Goetz
#

import json, logging, traceback
import dateutil.parser

import FileProcessor


logger = logging.getLogger(__file__)


class JsonFileProcessor(object):

    def __init__(self, input_file, input_dir, file_regex, latest, debug):
        self.debug = debug
        logger.info("Debug: %s" % str(debug))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, file_regex)
            logger.info("Found %d json files for %s in %s", self.file_count(), file_regex, input_file)
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, file_regex, latest)
            logger.info("Found %d json files for %s in %s", self.file_count(), file_regex, input_dir)

    def file_count(self):
        return len(self.file_names)

    def parse_file(self, filename):
        def parser(entry):
            for (conversion_key, conversion_func) in self.conversions.iteritems():
                entry_value = entry.get(conversion_key, None)
                if entry_value is not None:
                    entry[conversion_key] = conversion_func(entry_value)
            return entry
        return json.load(open(filename), object_hook=parser)

    def get_field(self, json, fieldname, format_func=str):
        try:
            data = json[fieldname]
            if data is not None:
                return format_func(data)
        except KeyError as e:
            logger.debug("JSON %s not found in %s: %s", fieldname, repr(json), str(e))

    def get_field_obj(self, json, fieldname, format_func):
        try:
            data = json[fieldname]
            return format_func(data)
        except KeyError as e:
            logger.debug("JSON %s not found in %s: %s", fieldname, repr(json), str(e))

    def process_json(self, json_data):
        pass

    def commit(self):
        pass

    def process_files(self):
        logger.info("Processing %d json files", self.file_count())
        for file_name in self.file_names:
            try:
                json_data = self.parse_file(file_name)
                updates = self.process_json(json_data)
                if updates > 0:
                    logger.info("DB updated with %d entries from %s", updates, file_name)
                else:
                    logger.info("No data saved for %s", file_name)
            except Exception as e:
                logger.error("Failed to parse %s: %s", file_name, traceback.format_exc())
            self.commit()
        logger.info("DB updated with %d entries.", self.file_count())

    def process(self):
        self.process_files()
