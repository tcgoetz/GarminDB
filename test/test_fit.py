#!/usr/bin/env python

"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import sys
import datetime
import re

sys.path.append('../.')

import Fit
from file_processor import FileProcessor


root_logger = logging.getLogger()
handler = logging.FileHandler('fit.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestFit(unittest.TestCase):
    """Class for testing FIT file parsing."""

    @classmethod
    def setUpClass(cls):
        cls.measurement_system = Fit.field_enums.DisplayMeasure.statute
        cls.file_path = 'test_files/fit'

    def check_message_types(self, fit_file, dump_message=False):
        unknown_messages = []
        message_types = fit_file.message_types()
        for message_type in message_types:
            if message_type.name.startswith('unknown'):
                if message_type.name not in unknown_messages:
                    logger.info("Unknown message type: %s in %s", message_type.name, fit_file.type())
                    unknown_messages.append(message_type.name)
            messages = fit_file[message_type]
            for message in messages:
                if dump_message:
                    logger.info("Message: %r", message)
                self.check_message_fields(message_type, message)

    def check_message_fields(self, message_type, message):
        unknown_message_fields = {}
        self.check_timestamp(message)
        self.check_temperature(message)
        for field_name in message:
            field_value = message[field_name]
            if not field_value.is_invalid() and field_name.startswith('unknown'):
                if message_type not in unknown_message_fields:
                    logger.info("Unknown %s message field: %s value %s", message_type, field_name, field_value.value)
                    unknown_message_fields[message_type] = [field_name]
                elif field_name not in unknown_message_fields[message_type]:
                    logger.info("Unknown %s message field: %s value: %s", message_type, field_name, field_value.value)
                    unknown_message_fields[message_type].append(field_name)

    def check_value(self, fit_file, message, key, expected_value):
        if key in message:
            value = message[key].value
            self.assertEqual(value, expected_value, 'file %s expected %r found %r' % (fit_file.filename, expected_value, value))

    def check_value_range(self, message, key, min_value, max_value):
        if key in message:
            value = message[key].value
            self.assertGreaterEqual(value, min_value)
            self.assertLess(value, max_value)

    def check_timestamp(self, message):
        self.check_value_range(message, 'timestamp', datetime.datetime(2000, 1, 1), datetime.datetime.now())

    def check_temperature(self, message):
        for field_name in message:
            if re.search('temperature_?\a{3}', field_name):
                logger.info("checking " + field_name)
                self.check_value_range(message, field_name, 0, 100)

    def check_file_id(self, fit_file, file_type):
        messages = fit_file[Fit.MessageType.file_id]
        for message in messages:
            self.check_value(fit_file, message, 'manufacturer', Fit.field_enums.Manufacturer.Garmin)
            self.check_value(fit_file, message, 'type', file_type)

    def check_monitoring_file(self, filename):
        fit_file = Fit.file.File(filename, self.measurement_system)
        self.check_message_types(fit_file)
        logger.info(filename + ' message types: %s', fit_file.message_types())
        self.check_file_id(fit_file, Fit.field_enums.FileType.monitoring_b)
        messages = fit_file[Fit.MessageType.monitoring]
        for message in messages:
            self.check_message_fields(message.type(), message)
            self.check_value_range(message, 'distance', 0, 100 * 5280)
            self.check_value_range(message, 'cum_ascent', 0, 5280)
            self.check_value_range(message, 'cum_descent', 0, 5280)

    def test_parse_monitoring(self):
        monitoring_path = self.file_path + '/monitoring'
        file_names = FileProcessor.dir_to_files(monitoring_path, Fit.file.name_regex, False)
        for file_name in file_names:
            self.check_monitoring_file(file_name)

    def check_lap_or_record(self, message):
        self.check_message_fields(message.type(), message)
        if 'distance' in message and message['distance'].value > 0.1:
            self.check_value_range(message, 'distance', 0, 100 * 5280)
            self.check_value_range(message, 'avg_vertical_oscillation', 0, 10)
            self.check_value_range(message, 'step_length', 0, 64)
            self.check_value_range(message, 'speed', 0, 100)

    def check_activity_file(self, filename):
        fit_file = Fit.file.File(filename, self.measurement_system)
        logger.info(filename + ' message types: %s', fit_file.message_types())
        self.check_message_types(fit_file, dump_message=True)
        self.check_file_id(fit_file, Fit.field_enums.FileType.activity)
        for message in fit_file[Fit.MessageType.record]:
            self.check_lap_or_record(message)
        for message in fit_file[Fit.MessageType.lap]:
            self.check_lap_or_record(message)
        for message in fit_file[Fit.MessageType.session]:
            self.check_lap_or_record(message)

    def test_parse_activity(self):
        activity_path = self.file_path + '/activity'
        file_names = FileProcessor.dir_to_files(activity_path, Fit.file.name_regex, False)
        for file_name in file_names:
            self.check_activity_file(file_name)

    def check_sleep_file(self, filename):
        fit_file = Fit.file.File(filename, self.measurement_system)
        logger.info(filename + ' message types: %s', fit_file.message_types())
        self.check_message_types(fit_file, dump_message=True)
        self.check_file_id(fit_file, Fit.field_enums.FileType.sleep)

    def test_parse_sleep(self):
        activity_path = self.file_path + '/sleep'
        file_names = FileProcessor.dir_to_files(activity_path, Fit.file.name_regex, False)
        for file_name in file_names:
            self.check_sleep_file(file_name)

    def check_unknown_file(self, filename):
        logger.info('Parsing ' + filename)
        fit_file = Fit.file.File(filename, self.measurement_system)
        logger.info(filename + ' message types: %s', fit_file.message_types())
        self.check_message_types(fit_file, dump_message=True)

    def test_parse_unknown(self):
        # root_logger.setLevel(logging.DEBUG)
        activity_path = self.file_path + '/unknown'
        file_names = FileProcessor.dir_to_files(activity_path, Fit.file.name_regex, False)
        for file_name in file_names:
            self.check_unknown_file(file_name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
