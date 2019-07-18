"""Utility functions."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


def list_in_list(list1, list2):
    """Test if all items in list1 are present in list2."""
    for list_item in list1:
        if list_item not in list2:
            return False
    return True


def list_intersection(list1, list2):
    """Return a list of the items present both in list1 and list2."""
    return [list_item for list_item in list1 if list_item in list2]


def list_intersection_count(list1, list2):
    """Return the count of itmes present in both lists."""
    return len(list_intersection(list1, list2))


def dict_filter_none_values(in_dict):
    """Given a dictionary, return a new dictionary with all of the non-None items."""
    return {key : value for key, value in in_dict.iteritems() if value is not None}


def filter_dict_by_list(in_dict, keep_list):
    """Return a dictionary with all items from the input dictionary who's keys appear in the list."""
    return {key : value for key, value in in_dict.iteritems() if key in keep_list}
