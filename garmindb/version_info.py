"""Version information for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


python_required = (3, 10, 0)
dev_python_required = (3, 13, 5)
python_tested = (3, 13, 5)
version_info = (3, 6, 6)
prerelease = True


def version_string():
    """Return a version string for a version tuple."""
    return '.'.join(str(digit) for digit in version_info)
