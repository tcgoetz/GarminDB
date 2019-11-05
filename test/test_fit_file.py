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
from utilities import FileProcessor


root_logger = logging.getLogger()
handler = logging.FileHandler('fit_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestFitFile(unittest.TestCase):
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
                self.check_message_fields(fit_file, message_type, message)

    def check_message_fields(self, fit_file, message_type, message):
        unknown_message_fields = {}
        self.check_timestamp(fit_file, message)
        self.check_temperature(message)
        self.check_sport_value(fit_file, message)
        for field_name in message:
            field_value = message[field_name]
            if not field_value.is_invalid() and field_name.startswith('unknown'):
                if message_type not in unknown_message_fields:
                    logger.info("Unknown %s message field: %s value %s", message_type, field_name, field_value.value)
                    unknown_message_fields[message_type] = [field_name]
                elif field_name not in unknown_message_fields[message_type]:
                    logger.info("Unknown %s message field: %s value: %s", message_type, field_name, field_value.value)
                    unknown_message_fields[message_type].append(field_name)

    def check_type(self, fit_file, message, key, expected_type):
        if key in message:
            value = message[key].value
            self.assertIsInstance(value, expected_type, 'file %s expected %r found %r' % (fit_file.filename, expected_type, value))
            logger.info("%s %r: %r", fit_file.filename, message.type, value)

    def check_value(self, fit_file, message, key, expected_value):
        if key in message:
            value = message[key].value
            self.assertEqual(value, expected_value, 'file %s expected %r found %r' % (fit_file.filename, expected_value, value))

    def check_value_range(self, fit_file, message, field_name, min_value, max_value):
        if field_name in message:
            value = message[field_name].value
            self.assertGreaterEqual(value, min_value, '%s %r %s expected greater than %r was %r' %
                                    (fit_file.filename, message.type(), field_name, min_value, value))
            self.assertLess(value, max_value, '%s %r %s expected less than %r was %r' %
                            (fit_file.filename, message.type(), field_name, max_value, value))

    def check_timestamp(self, fit_file, message):
        # Garmin Connect generated files can have device dates far in the future
        if message.type() != Fit.MessageType.device_info and message.get('product') != Fit.field_enums.GarminProduct.connect:
            self.check_value_range(fit_file, message, 'timestamp', datetime.datetime(2000, 1, 1), datetime.datetime.now())

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

    def check_sport_value(self, fit_file, message):
        self.check_type(fit_file, message, 'sport', Fit.field_enums.Sport)
        self.check_type(fit_file, message, 'sub_sport', Fit.field_enums.SubSport)

    def check_sport(self, fit_file):
        sport_messages = fit_file[Fit.MessageType.sport]
        if sport_messages:
            for sport_message in sport_messages:
                self.check_sport_value(fit_file, sport_message)
            sport = sport_messages[0].get('sport')
            sub_sport = sport_messages[0].get('sub_sport')
            logger.info("%s: %r %r", fit_file.filename, sport, sub_sport)
            return sport

    def check_monitoring_file(self, filename):
        fit_file = Fit.file.File(filename, self.measurement_system)
        self.check_message_types(fit_file)
        logger.info(filename + ' message types: %s', fit_file.message_types())
        self.check_file_id(fit_file, Fit.field_enums.FileType.monitoring_b)
        messages = fit_file[Fit.MessageType.monitoring]
        for message in messages:
            self.check_message_fields(fit_file, message.type(), message)
            self.check_value_range(fit_file, message, 'distance', 0, 100 * 5280)
            self.check_value_range(fit_file, message, 'cum_ascent', 0, 5280)
            self.check_value_range(fit_file, message, 'cum_descent', 0, 5280)

    def test_parse_monitoring(self):
        monitoring_path = self.file_path + '/monitoring'
        file_names = FileProcessor.dir_to_files(monitoring_path, Fit.file.name_regex, False)
        for file_name in file_names:
            self.check_monitoring_file(file_name)

    def check_step_lap_or_record(self, message):
        self.check_value_range(message, 'distance', 0, 100 * 5280)
        self.check_value_range(message, 'avg_vertical_oscillation', 0, 10)
        self.check_value_range(message, 'step_length', 0, 64)
        self.check_value_range(message, 'speed', 0, 100)

    def check_lap_or_record(self, fit_file, sport, message):
        self.check_message_fields(fit_file, message.type(), message)
        if 'distance' in message and message['distance'].value > 0.1:
            if sport == Fit.field_enums.Sport.running or sport == Fit.field_enums.Sport.walking:
                self.check_step_lap_or_record(message)

    def check_activity_file(self, filename):
        fit_file = Fit.file.File(filename, self.measurement_system)
        logger.info(filename + ' message types: %s', fit_file.message_types())
        self.check_message_types(fit_file, dump_message=True)
        self.check_file_id(fit_file, Fit.field_enums.FileType.activity)
        sport = self.check_sport(fit_file)
        for message in fit_file[Fit.MessageType.record]:
            self.check_lap_or_record(fit_file, sport, message)
        for message in fit_file[Fit.MessageType.lap]:
            self.check_lap_or_record(fit_file, sport, message)
        for message in fit_file[Fit.MessageType.session]:
            self.check_lap_or_record(fit_file, sport, message)

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
