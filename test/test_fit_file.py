"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime
import re

import fitfile
from idbutils import FileProcessor


root_logger = logging.getLogger()
handler = logging.FileHandler('fit_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


test_activity_files     = True
test_monitoring_files   = True
test_sleep_files        = True
test_metrics_files      = True
test_unknown_files      = True


class TestFitFile(unittest.TestCase):
    """Class for testing FIT file parsing."""

    @classmethod
    def setUpClass(cls):
        cls.measurement_system = fitfile.field_enums.DisplayMeasure.statute
        cls.file_path = 'test_files/fit'

    def check_message_fields(self, fit_file, message_type, message):
        unknown_message_fields = {}
        self.check_timestamp(fit_file, message)
        self.check_temperature(message)
        self.check_sport_value(fit_file, message)
        for field_name in message.field_values:
            if not message.field_values[field_name].is_invalid() and field_name.startswith('unknown'):
                if message_type not in unknown_message_fields:
                    logger.info("Unknown %s message field: %s value %s", message_type, field_name, message.fields[field_name])
                    unknown_message_fields[message_type] = [field_name]
                elif field_name not in unknown_message_fields[message_type]:
                    logger.info("Unknown %s message field: %s value: %s", message_type, field_name, message.fields[field_name])
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

    def check_type(self, fit_file, message, key, expected_type):
        if key in message.fields:
            value = message.fields[key]
            self.assertIsInstance(value, expected_type, 'file %s expected %r found %r' % (fit_file.filename, expected_type, value))
            logger.info("%s %r: %r", fit_file.filename, message.type, value)

    def check_value(self, fit_file, message, field_name, expected_value):
        if field_name in message.fields:
            value = message.fields[field_name]
            self.assertEqual(value, expected_value, 'file %s expected %r found %r' % (fit_file.filename, expected_value, value))

    def check_value_range(self, fit_file, message, field_name, min_value, max_value, round_value=False):
        if field_name in message.fields:
            value = message.fields[field_name]
            if value is not None:
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
                                   datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc))

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
        if fit_file.product != fitfile.GarminProduct.connect:
            self.check_timestamp_delta(fit_file, self.start_time, self.end_time, (0, 86400))
        for message in fit_file.file_id:
            self.check_value(fit_file, message, 'manufacturer', fitfile.Manufacturer.Garmin)
            self.check_value(fit_file, message, 'type', file_type)

    def check_sport_value(self, fit_file, message):
        self.check_type(fit_file, message, 'sport', fitfile.Sport)
        self.check_type(fit_file, message, 'sub_sport', fitfile.SubSport)

    def check_sport(self, fit_file):
        sport = None
        sub_sport = None
        for sport_message in fit_file.sport:
            self.check_sport_value(fit_file, sport_message)
            sport = sport_message.fields.sport
            sub_sport = sport_message.fields.sub_sport
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
        if sport == fitfile.Sport.running or sport == fitfile.Sport.walking or sub_sport == fitfile.SubSport.elliptical:
            self.check_step_record(fit_file, message_index, message)

    def check_lap_or_session(self, fit_file, sport, sub_sport, message_index, message):
        self.check_message_fields(fit_file, message.type, message)
        if sport == fitfile.Sport.running or sport == fitfile.Sport.walking or sub_sport == fitfile.SubSport.elliptical:
            self.check_step_lap_or_session(fit_file, message_index, message)

    def check_monitoring_messages(self, fit_file):
        last_steps = {}
        last_timestamp = None
        for message in fit_file.monitoring:
            if 'steps' in message.fields:
                steps = message.fields.steps
                activity_type = message.fields.activity_type
                if activity_type in last_steps:
                    activity_last_steps = last_steps[activity_type]
                    self.assertGreaterEqual(steps, activity_last_steps, f'{fit_file.filename}: {repr(message)} - steps not greater than last steps')
                last_steps[activity_type] = steps
                if last_timestamp:
                    self.check_timestamp_delta(fit_file, last_timestamp, message.fields.timestamp, (0, 43200))
                last_timestamp = message.fields.timestamp
            self.check_message_fields(fit_file, message.type, message)
            self.check_value_range(fit_file, message, 'distance', 0, 100 * 5280, True)
            self.check_value_range(fit_file, message, 'cum_ascent', 0, 5280, True)
            self.check_value_range(fit_file, message, 'cum_descent', 0, 5280, True)

    def check_monitoring_file(self, filename):
        fit_file = fitfile.file.File(filename, self.measurement_system)
        self.check_message_types(fit_file, dump_message=True)
        logger.info('%s (%s) monitoring file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        self.check_file_id(fit_file, fitfile.FileType.monitoring_b)
        self.check_monitoring_messages(fit_file)

    def check_activity_file(self, filename):
        fit_file = fitfile.file.File(filename, self.measurement_system)
        logger.info('%s (%s) activity file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        self.check_message_types(fit_file, dump_message=True)
        self.check_file_id(fit_file, fitfile.FileType.activity)
        (sport, sub_sport) = self.check_sport(fit_file)
        for message_index, message in enumerate(fit_file.record):
            self.check_record(fit_file, sport, sub_sport, message_index, message)
        for message_index, message in enumerate(fit_file.lap):
            self.check_lap_or_session(fit_file, sport, sub_sport, message_index, message)
        for message_index, message in enumerate(fit_file.session):
            self.check_lap_or_session(fit_file, sport, sub_sport, message_index, message)

    def check_sleep_file(self, filename):
        fit_file = fitfile.file.File(filename, self.measurement_system)
        logger.info('%s (%s) sleep file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        self.check_message_types(fit_file, dump_message=True)
        self.check_file_id(fit_file, fitfile.FileType.sleep)

    def check_unknown_file(self, filename):
        logger.info('Parsing ' + filename)
        fit_file = fitfile.file.File(filename, self.measurement_system)
        logger.info('%s (%s) unknown file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        self.check_message_types(fit_file, dump_message=True)

    #
    # The tests
    #
    @unittest.skipIf(not test_monitoring_files, 'Test not selected')
    def test_parse_monitoring(self):
        monitoring_path = self.file_path + '/monitoring'
        file_names = FileProcessor.dir_to_files(monitoring_path, fitfile.file.name_regex, False)
        for file_name in file_names:
            self.check_monitoring_file(file_name)

    @unittest.skipIf(not test_activity_files, 'Test not selected')
    def test_parse_activity(self):
        activity_path = self.file_path + '/activity'
        file_names = FileProcessor.dir_to_files(activity_path, fitfile.file.name_regex, False)
        for file_name in file_names:
            self.check_activity_file(file_name)

    @unittest.skipIf(not test_sleep_files, 'Test not selected')
    def test_parse_sleep(self):
        activity_path = self.file_path + '/sleep'
        file_names = FileProcessor.dir_to_files(activity_path, fitfile.file.name_regex, False)
        for file_name in file_names:
            self.check_sleep_file(file_name)

    @unittest.skipIf(not test_metrics_files, 'Test not selected')
    def test_parse_metrics(self):
        # root_logger.setLevel(logging.DEBUG)
        activity_path = self.file_path + '/metrics'
        file_names = FileProcessor.dir_to_files(activity_path, fitfile.file.name_regex, False)
        for file_name in file_names:
            self.check_unknown_file(file_name)

    @unittest.skipIf(not test_unknown_files, 'Test not selected')
    def test_parse_unknown(self):
        # root_logger.setLevel(logging.DEBUG)
        activity_path = self.file_path + '/unknown'
        file_names = FileProcessor.dir_to_files(activity_path, fitfile.file.name_regex, False)
        for file_name in file_names:
            self.check_unknown_file(file_name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
