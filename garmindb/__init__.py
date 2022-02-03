"""A database and database objects for storing health data from Garmin Connect."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

# flake8: noqa

from .version_info import version_string

__version__ = version_string()

from .activity_fit_plugin_base import ActivityFitPluginBase
from .monitoring_fit_plugin_base import MonitoringFitPluginBase
from .activity_fit_file_processor import ActivityFitFileProcessor
from .fit_data import FitData
from .fit_file_processor import FitFileProcessor
from .garmin_connect_config_manager import GarminConnectConfigManager
from .config_manager import ConfigManager
from .statistics import Statistics
from .tcx import Tcx
from .monitoring_fit_file_processor import MonitoringFitFileProcessor
from .export_activities import ActivityExporter
from .open_with_basecamp import OpenWithBaseCamp
from .open_with_google_earth import OpenWithGoogleEarth

from .graphs import Graph
from .maps import Map, ActivityMap
from .checkup import Checkup

from .copy import Copy
from .download import Download
from .analyze import Analyze
from .plugin_manager import PluginManager
from .version import format_version, log_version, python_version_check

from .import_monitoring import GarminMonitoringFitData, GarminSummaryData, GarminProfile, GarminWeightData, GarminSleepData, GarminRhrData, GarminSettingsFitData, GarminHydrationData
from .activities_fit_data import GarminActivitiesFitData
from .garmin_tcx_data import GarminTcxData
from .garmin_json_data import GarminJsonSummaryData, GarminJsonDetailsData
