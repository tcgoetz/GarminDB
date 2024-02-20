"""Version information for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import idbutils.version as uv

from .version_info import dev_python_required, python_required, python_tested, version_info, prerelease


version_string = uv.to_string(version_info, prerelease)


def format_version(program):
    """Print version information for the script."""
    return uv.format(program, version_string)


def log_version(program):
    """Print version information for the script."""
    uv.log(program, version_string)


def python_version_check(program):
    """Validate the Python version requirements for a pip installed package."""
    uv.python_version_check(program, python_required, python_tested)


def python_dev_version_check(program):
    """Validate the Python version requirements for development."""
    uv.python_version_check(program, dev_python_required, python_tested, verbose=True)
