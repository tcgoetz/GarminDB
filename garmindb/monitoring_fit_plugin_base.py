"""Base class for GarminDb plugins."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging


logger = logging.getLogger(__file__)


class MonitoringFitPluginBase():
    """Base class for GarminDb monitoring FIT file plugins."""

    _type = 'MonitoringFit'

    @classmethod
    def matches_monitoring_file(cls, fit_file):
        """Return if the file matches this plugin."""
        return True

    @classmethod
    def init_monitoring(cls, act_db_class, monitoring_table):
        """Initialize an instance of the plugin as an monitoring FIT file plugin."""
        logger.info("Initializing tables for monitoring plugin %s with monitoring table %s", cls.__name__, monitoring_table)
