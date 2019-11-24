"""Version information for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import utilities.version as uv


python_required = (3, 0, 0)
python_tested = (3, 7, 5)

version_info = (1, 1, 0)
version_string = uv.to_string(version_info)


def print_version(program):
    """Print version information for the script."""
    uv.display(program, version_string)


def log_version(program):
    """Print version information for the script."""
    uv.log(program, version_string)


def python_version_check(program):
    """Validate the Python version requirements."""
    uv.python_version_check(program, python_required, python_tested)
