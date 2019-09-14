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


root_logger = logging.getLogger()
handler = logging.FileHandler('fit_field_enum.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestFitFieldEnum(unittest.TestCase):
    """Class for testing FIT file parsing."""

    @classmethod
    def setUpClass(cls):
        pass

    def test_field_enum_valid_conversion(self):
        self.assertEqual(Fit.field_enums.Switch.from_string('on'), Fit.field_enums.Switch.on)

    def test_field_enum_unknown_conversion(self):
        self.assertIsInstance(Fit.field_enums.Switch.from_string('junk'), Fit.field_enums.UnknownEnumValue)

    def test_field_enum_fuzzy_conversion(self):
        self.assertEqual(Fit.field_enums.DisplayMeasure.from_string('metric_system'), Fit.field_enums.DisplayMeasure.metric)

    def test_enum_field_valid_conversion(self):
        switch = Fit.fields.SwitchField()
        field_value = switch.convert(1, 255)
        self.assertEqual(field_value.value, Fit.field_enums.Switch.on)

    def test_enum_field_unknown_conversion(self):
        switch = Fit.fields.SwitchField()
        field_value = switch.convert(10, 255)
        self.assertIsInstance(field_value.value, Fit.field_enums.UnknownEnumValue)


if __name__ == '__main__':
    unittest.main(verbosity=2)
