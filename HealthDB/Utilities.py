#
# copyright Tom Goetz
#


def list_in_list(list1, list2):
    for list_item in list1:
        if list_item not in list2:
            return False
    return True


def list_intersection(list1, list2):
    return [list_item for list_item in list1 if list_item in list2]


def list_intersection_count(list1, list2):
    return len(list_intersection(list1, list2))


def dict_filter_none_values(in_dict):
    return {key : value for key, value in in_dict.iteritems() if value is not None}


def filter_dict_by_list(in_dict, keep_list, ignore_list=[]):
    return {key : value for key, value in in_dict.iteritems() if key in keep_list and key not in ignore_list}
