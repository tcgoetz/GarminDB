"""Utility functions for Jupyter notebooks."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import snakemd


def format_number(number, digits=0):
    """Format a number for display."""
    if number is not None:
        return round(number, digits)
    return '-'


def format_string(string):
    """Format a string for display."""
    if string is not None:
        return string
    return '-'


def format_temp(temp, digits=1):
    """Format a tempature value for display."""
    return format_number(temp, digits)


def format_distance(distance, digits=1):
    """Format a distance value for display."""
    return format_number(distance, digits)


def format_weight(distance, digits=1):
    """Format a weight value for display."""
    return format_number(distance, digits)


def linked_location(location):
    """Return a location as markdown formatted linked text."""
    return snakemd.Inline(location.display(), location.to_google_maps_url())
