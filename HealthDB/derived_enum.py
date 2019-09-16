"""Functions for deriving enums from other enums."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import enum


@classmethod
def _convert(cls, parent_enum_value):
    if parent_enum_value is not None:
        try:
            return getattr(cls, cls.prefix + parent_enum_value.name)
        except Exception:
            return parent_enum_value


@classmethod
def _from_string_ext(cls, string):
    """Return an instance of enun instantiated with string using a fuzzy match."""
    for name, value in cls.__members__.items():
        if name in str(string):
            return value


@classmethod
def _from_string(cls, string):
    """Return an instance of enum instantiated with string."""
    try:
        try:
            return cls(string)
        except Exception:
            return getattr(cls, string)
    except (AttributeError, TypeError):
        return cls.from_string_ext(string)


def derive(name, parent_enum, names_and_values_dict, prefix=''):
    """Return a new Enum with the names and values of the parent enum added to the supplied dict's name and values."""
    all_names_and_values = {prefix + p.name : p.value for p in parent_enum}
    all_names_and_values.update(names_and_values_dict)
    new_enum = enum.Enum(name, names=all_names_and_values)
    setattr(new_enum, 'prefix', prefix)
    setattr(new_enum, 'convert', _convert)
    setattr(new_enum, 'from_string', _from_string)
    setattr(new_enum, 'from_string_ext', _from_string_ext)
    return new_enum
