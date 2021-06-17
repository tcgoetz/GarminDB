"""Version information for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import idbutils.version as uv

from .version_info import python_required, python_tested, version_info, prerelease


version_string = uv.to_string(version_info, prerelease)


def format_version(program):
    """Print version information for the script."""
    return uv.format(program, version_string)


def log_version(program):
    """Print version information for the script."""
    uv.log(program, version_string)


def python_version_check(program):
    """Validate the Python version requirements."""
    uv.python_version_check(program, python_required, python_tested)
