"""Version information for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


python_required = (3, 0, 0)
python_tested = (3, 9, 5)
version_info = (3, 2, 2)
prerelease = False


def version_string():
    """Return a version string for a version tuple."""
    return '.'.join(str(digit) for digit in version_info)
