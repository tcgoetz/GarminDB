"""Base classes for plugins."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging

import idbutils

from .garmindb import ActivitiesDb, Activities


logger = logging.getLogger(__file__)


class PluginManager(idbutils.PluginManager):
    """Loads python file based plugins that extend GarminDb."""

    def __init__(self, plugin_dir, db_params):
        """Load python file based plugins from plugin_dir."""
        logger.info("Loading GarminDb plugins from %s", plugin_dir)
        super().__init__(plugin_dir, {'db_params': db_params})

    def get_file_processors(self, file_type, fit_file):
        """Return a dict of all plugins that handle file_type."""
        result = {}
        if file_type in self.plugins:
            for plugin_name, plugin in self.plugins[file_type].items():
                if plugin.matches_activity_file(fit_file):
                    logger.info("Activity Fit plugin %s matches file %s", plugin_name, fit_file)
                    plugin.init_activity(ActivitiesDb, Activities)
                    result[plugin_name] = plugin
        return result
