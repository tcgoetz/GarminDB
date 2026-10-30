"""Test importing monitoring FIT files whose UTC offset changes during the file."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

import fitfile

from garmindb import MonitoringFitFileProcessor


root_logger = logging.getLogger()
handler = logging.FileHandler('monitoring_fit_file_processor.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

utc = datetime.timezone.utc


class FakeMessage():
    """Stands in for a monitoring_info message."""

    def __init__(self, timestamp, local_timestamp):
        """Return a message that has only the fields the processor reads."""
        self.fields = {'timestamp': timestamp, 'local_timestamp': local_timestamp}


class FakeFitFile():
    """Stands in for a fitfile.File."""

    utc_offset = 3600.0

    def __init__(self, monitoring_infos):
        """Return a file with the given monitoring_info messages."""
        self.monitoring_infos = monitoring_infos

    def __getitem__(self, message_type):
        return self.monitoring_infos if message_type is fitfile.MessageType.monitoring_info else []


class TestUtcOffsetChange(unittest.TestCase):
    """Test that each timestamp is converted with the UTC offset in effect at that time."""

    def test_offset_per_segment(self):
        fit_file = FakeFitFile([
            FakeMessage(datetime.datetime(2026, 10, 24, 23, 0, tzinfo=utc), datetime.datetime(2026, 10, 25, 0, 0)),
            FakeMessage(datetime.datetime(2026, 10, 25, 1, 1, tzinfo=utc), datetime.datetime(2026, 10, 25, 1, 1)),
        ])
        processor = MonitoringFitFileProcessor.__new__(MonitoringFitFileProcessor)
        processor._set_utc_offsets(fit_file)

        def convert(*args):
            return processor._utc_datetime_to_local(fit_file, datetime.datetime(*args, tzinfo=utc))

        self.assertEqual(convert(2026, 10, 24, 23, 0), datetime.datetime(2026, 10, 25, 0, 0))
        self.assertEqual(convert(2026, 10, 25, 1, 0), datetime.datetime(2026, 10, 25, 2, 0))
        self.assertEqual(convert(2026, 10, 25, 1, 1), datetime.datetime(2026, 10, 25, 1, 1))
        self.assertEqual(convert(2026, 10, 26, 0, 0), datetime.datetime(2026, 10, 26, 0, 0))

    def test_offset_before_first_monitoring_info_is_file_offset(self):
        fit_file = FakeFitFile([FakeMessage(datetime.datetime(2026, 10, 25, 1, 1, tzinfo=utc), datetime.datetime(2026, 10, 25, 1, 1))])
        processor = MonitoringFitFileProcessor.__new__(MonitoringFitFileProcessor)
        processor._set_utc_offsets(fit_file)
        self.assertEqual(processor._utc_datetime_to_local(fit_file, datetime.datetime(2026, 10, 25, 0, 0, tzinfo=utc)), datetime.datetime(2026, 10, 25, 1, 0))

    def test_no_monitoring_info_is_file_offset(self):
        fit_file = FakeFitFile([])
        processor = MonitoringFitFileProcessor.__new__(MonitoringFitFileProcessor)
        processor._set_utc_offsets(fit_file)
        self.assertEqual(processor._utc_datetime_to_local(fit_file, datetime.datetime(2026, 10, 25, 5, 0, tzinfo=utc)), datetime.datetime(2026, 10, 25, 6, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
