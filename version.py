"""Version information for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


version_info = (1, 1, 0)
version = '.'.join(str(digit) for digit in version_info)


def print_version(program):
    """Print version information for the script."""
    print('%s' % version)
