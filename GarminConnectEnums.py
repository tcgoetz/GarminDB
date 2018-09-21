#!/usr/bin/env python

#
# copyright Tom Goetz
#


import enum, logging


logger = logging.getLogger(__file__)


class Event(enum.Enum):
    race            = 1
    recreation      = 2
    fitness         = 8
    uncategorized   = 9

    @classmethod
    def from_json(cls, json_data):
        json_event = json_data['eventType']
        try:
            return cls(json_event['typeId'])
        except ValueError:
            logger.info("Unknown event type: %s", repr(json_event))
            raise


class Sport(enum.Enum):
    running                         = 1
    cycling                         = 2
    hiking                          = 3
    other                           = 4
    mountain_biking                 = 5
    walking                         = 9
    strength_training               = 13
    top_level                       = 17
    treadmill_running               = 18
    fitness_equipment               = 29
    elliptical                      = 30
    snow_shoe                       = 36
    paddling                        = 57
    inline_skating                  = 63
    resort_skiing_snowboarding      = 67
    stand_up_paddleboarding         = 87

    @classmethod
    def from_json(cls, json_data):
        json_activity = json_data['activityType']
        try:
            return Sport(json_activity['parentTypeId'])
        except ValueError:
            logger.info("Unknown sport type: %s", repr(json_activity))
            raise

    @classmethod
    def subsport_from_json(cls, json_data):
        json_activity = json_data['activityType']
        try:
            return Sport(json_activity['typeId'])
        except ValueError:
            logger.info("Unknown subsport type: %s", repr(json_activity))
            raise
