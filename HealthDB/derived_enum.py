"""Functions for deriving enums from other enums."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import enum


@classmethod
def _convert(cls, parent_enum_value):
    if parent_enum_value is not None:
        return getattr(cls, cls.prefix + parent_enum_value.name)


def derive(name, parent_enum, names_and_values_dict, prefix=''):
    """Return a new Enum with the names and values of the parent enum added to the supplied dict's name and values."""
    all_names_and_values = {prefix + p.name : p.value for p in parent_enum}
    all_names_and_values.update(names_and_values_dict)
    new_enum = enum.Enum(name, names=all_names_and_values)
    setattr(new_enum, 'prefix', prefix)
    setattr(new_enum, 'convert', _convert)
    return new_enum
