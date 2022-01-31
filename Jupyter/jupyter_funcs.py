"""Utility functions for Jupyter notebooks."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


def format_number(number, digits=0):
    """Format a number for display."""
    if number is not None:
        return round(number, digits)
    return ''
