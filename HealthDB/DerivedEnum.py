#!/usr/bin/env python

#
# copyright Tom Goetz
#

import enum


@classmethod
def convert(cls, parent_enum_value):
    if parent_enum_value is not None:
        return getattr(cls, cls.prefix + parent_enum_value.name)

def derived_enum(name, parent_enum, names_and_values_dict, prefix=''):
    all_names_and_values = {prefix + p.name : p.value for p in parent_enum}
    all_names_and_values.update(names_and_values_dict)
    new_enum = enum.Enum(name, names=all_names_and_values)
    setattr(new_enum, 'prefix', prefix)
    setattr(new_enum, 'convert', convert)
    return new_enum

