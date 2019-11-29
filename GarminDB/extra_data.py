"""Objects representing a databse objects for storing extra data attached to another record."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import enum
import re
import json
from sqlalchemy import Column, String, Enum

import utilities


class FuzzyMatchEnum(enum.Enum):
    @classmethod
    def from_string_ext(cls, string):
        for name, value in cls.__members__.items():
            if name.lower() in string.lower():
                return value

    @classmethod
    def from_string(cls, string):
        try:
            try:
                return cls(string)
            except Exception:
                return getattr(cls, string)
        except AttributeError:
            return cls.from_string_ext(string)


class Mood(FuzzyMatchEnum):
    Excited     = 1
    Happy       = 2
    Good        = 3
    Sad         = 4
    Depressed   = 5


class Condition(FuzzyMatchEnum):
    Rested      = 1
    Healthy     = 2
    Tired       = 3
    Sick        = 4


class ExtraData(utilities.DBObject):

    mood = Column(Enum(Mood))
    condition = Column(Enum(Condition))
    weather = Column(String)
    text = Column(String)
    people = Column(String)

    @classmethod
    def from_string(cls, string):
        if string is not None:
            match = re.match(r'(.*)(\{.+\})', string, re.M | re.S)
            if match:
                return (match.group(1), json.loads(match.group(2)))
            return (string, None)
        return (None, None)

    @classmethod
    def convert_eums(cls, extra_data):
        mood = extra_data.get('mood')
        if mood is not None:
            extra_data['mood'] = Mood.from_string(mood)
        condition = extra_data.get('condition')
        if condition is not None:
            extra_data['condition'] = Condition.from_string(condition)
        return extra_data
