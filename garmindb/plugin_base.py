"""Base class for GarminDb plugins."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging


logger = logging.getLogger(__file__)


class PluginBase():
    """Base class for GarminDb file plugins."""

    @classmethod
    def _get_field(cls, message_fields, field_name_list):
        for field_name in field_name_list:
            if field_name in message_fields:
                return message_fields[field_name]

    @classmethod
    def filter_data(cls, indict):
        """Filter None and 0 values from a dict."""
        return {key: value for key, value in indict.items() if value}

    def __str__(self):
        """Return a string representation of the class instance."""
        return f'{self.__class__.__name__}(tables {repr(self._tables.keys())})'
