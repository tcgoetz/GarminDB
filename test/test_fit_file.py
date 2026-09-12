"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime
import re

import fitfile


root_logger = logging.getLogger()
logger = logging.getLogger(__name__)


class TestFitFile(unittest.TestCase):
    """Class for testing FIT file parsing."""

    @classmethod
    def setUpClass(cls):
        cls.measurement_system = fitfile.MeasurementSystem.statute
        cls.file_path = 'test_files/fit'

    def check_message_fields(self, fit_file, message_type, message):
        unknown_message_fields = {}
        self.check_timestamp(fit_file, message)
        self.check_temperature(message)
        self.check_sport_value(fit_file, message)
        for field_name in message.field_values:
            if not message.field_values[field_name].is_invalid() and field_name.startswith('unknown'):
                if message_type not in unknown_message_fields:
                    logger.info("Unknown %s message field: %s value: %r", message_type, field_name, message.fields[field_name])
                    unknown_message_fields[message_type] = [field_name]
                elif field_name not in unknown_message_fields[message_type]:
                    logger.info("Unknown %s message field: %s value: %r", message_type, field_name, message.fields[field_name])
                    unknown_message_fields[message_type].append(field_name)

    def check_message_types(self, fit_file, dump_message=False):
        unknown_messages = []
        for message_type in fit_file.message_types:
            if message_type.name.startswith('unknown'):
                if message_type.name not in unknown_messages:
                    logger.info("Unknown message type: %s in %s", message_type.name, fit_file.type)
                    unknown_messages.append(message_type.name)
            messages = fit_file[message_type]
            for message in messages:
                if dump_message:
                    logger.info("Message: %r", message)
                self.check_message_fields(fit_file, message_type, message)

    def check_type(self, fit_file, message, field_name, expected_type):
        if field_name in message.fields:
            value = message.fields[field_name]
            self.assertIsInstance(value, expected_type, 'file %s field %s expected %r found %r' % (fit_file.filename, field_name, expected_type, value))
            logger.info("%s %r: %r", fit_file.filename, message.type, value)

    def check_value(self, fit_file, message, field_name, expected_value):
        if field_name in message.fields:
            value = message.fields[field_name]
            self.assertEqual(value, expected_value, 'file %s expected %r found %r' % (fit_file.filename, expected_value, value))

    def check_values(self, fit_file, message, field_name, expected_value_list):
        if field_name in message.fields:
            value = message.fields[field_name]
            self.assertIn(value, expected_value_list, 'file %s expected %r found %r' % (fit_file.filename, expected_value_list, value))

    def check_value_range(self, fit_file, message, field_name, min_value, max_value, round_value=False):
        if field_name in message.field_values and not message.field_values[field_name].is_invalid():
            value = message.fields[field_name]
            if value is not None and value:
                if round_value:
                    value = round(value)
                self.assertGreaterEqual(value, min_value, '%s expected greater than %r was %r: %s %r' %
                                        (field_name, min_value, value, fit_file.filename, message))
                self.assertLess(value, max_value, '%s expected less than %r was %r: %s %r ' %
                                (field_name, max_value, value, fit_file.filename, message))
                return True

    def check_timestamp(self, fit_file, message):
        # Garmin Connect generated files can have device dates far in the future
        if (message.type != fitfile.MessageType.device_info or message.type != fitfile.MessageType.file_id) and message.fields.product != fitfile.GarminProduct.connect:
            self.check_value_range(fit_file, message, 'timestamp',
                                   datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
                                   datetime.datetime.now(datetime.UTC))

    def check_temperature(self, message):
        for field_name in message.fields:
            if re.search('temperature_?\a{3}', field_name):
                logger.info("checking " + field_name)
                self.check_value_range(message, field_name, 0, 100)

    def check_timestamp_delta(self, fit_file, start_time, end_time, bounds):
        self.assertEqual(start_time.tzinfo, end_time.tzinfo, 'timezones do not match')
        self.assertGreaterEqual(start_time, self.start_time, 'timestamp before file start')
        self.assertLessEqual(end_time, self.end_time, 'timestamp after end of file')
        total_seconds_in_file = (end_time - start_time).total_seconds()
        self.assertGreaterEqual(total_seconds_in_file, bounds[0], f'time span ({start_time}, {end_time}) is negative')
        self.assertLessEqual(total_seconds_in_file, bounds[1], f'time for {fit_file.filename} span ({start_time}, {end_time}) greater than bound')

    def check_file_id(self, fit_file, file_type):
        self.assertGreaterEqual(fit_file.utc_offset, -36000, 'Is not a valid time zone offset')
        self.assertLessEqual(fit_file.utc_offset, +46800, 'Is not a valid time zone offset')
        # file contains less than a day span of time
        (self.start_time, self.end_time) = fit_file.date_span()
        for message in fit_file.file_id:
            self.check_value(fit_file, message, 'manufacturer', fitfile.Manufacturer.Garmin)
            self.check_value(fit_file, message, 'type', file_type)

    def check_sport_value(self, fit_file, message):
        self.check_type(fit_file, message, 'sport', fitfile.fields.Sport)
        self.check_type(fit_file, message, 'sub_sport', fitfile.fields.SubSport)

    def check_sport(self, fit_file):
        sport = None
        sub_sport = None
        for sport_message in fit_file.sport:
            self.check_sport_value(fit_file, sport_message)
            sport = sport_message.fields.sport
            sub_sport = sport_message.fields.sub_sport
        self.assertEqual(sport, fit_file.sport_type, 'file %s expected %r found %r' % (fit_file.filename, fit_file.sport_type, sport))
        self.assertEqual(sub_sport, fit_file.sub_sport_type, 'file %s expected %r found %r' % (fit_file.filename, fit_file.sub_sport_type, sub_sport))
        logger.info("%s: %r %r", fit_file.filename, sport, sub_sport)
        return (sport, sub_sport)

    def check_step_message(self, fit_file, message_index, message):
        self.check_value_range(fit_file, message, 'avg_vertical_oscillation', 0, 10)
        self.check_value_range(fit_file, message, 'step_length', 0, 64)
        self.check_value_range(fit_file, message, 'speed', 0, 25)

    def check_step_record(self, fit_file, message_index, message):
        self.check_value_range(fit_file, message, 'distance', 0, 100)
        self.check_step_message(fit_file, message_index, message)

    def check_step_lap_or_session(self, fit_file, message_index, message):
        self.check_value_range(fit_file, message, 'distance', 0, 100 * 5280)
        self.check_step_message(fit_file, message_index, message)

    def check_record(self, fit_file, sport, sub_sport, message_index, message):
        self.check_message_fields(fit_file, message.type, message)
        if sport == fitfile.fields.Sport.running or sport == fitfile.fields.Sport.walking or sub_sport == fitfile.fields.SubSport.elliptical:
            self.check_step_record(fit_file, message_index, message)

    def check_lap_or_session(self, fit_file, sport, sub_sport, message_index, message):
        self.check_message_fields(fit_file, message.type, message)
        if sport == fitfile.fields.Sport.running or sport == fitfile.fields.Sport.walking or sub_sport == fitfile.fields.SubSport.elliptical:
            self.check_step_lap_or_session(fit_file, message_index, message)

    def check_unknown_file(self, filename):
        logger.info('Parsing ' + filename)
        fit_file = fitfile.file.File(filename, self.measurement_system)
        logger.info('%s (%s) unknown file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        self.check_message_types(fit_file, dump_message=True)
