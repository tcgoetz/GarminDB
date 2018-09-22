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
    geocaching      = 7
    # special_event
    # touring
    # training
    # transportation
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
    trail_running                   = 6
    street_running                  = 7
    track_running                   = 8
    walking                         = 9
    road_biking                     = 10
    strength_training               = 13
    casual_walking                  = 15
    top_level                       = 17
    treadmill_running               = 18
    swimming                        = 26
    fitness_equipment               = 29
    elliptical                      = 30
    stair_climbing                  = 31
    snow_shoe                       = 36
    rowing                          = 39
    paddling                        = 57
    skating                         = 62
    inline_skating                  = 63
    resort_skiing_snowboarding      = 67
    cross_country_skiing            = 81
    stand_up_paddleboarding         = 87
    diving                          = 144
    indoor_running                  = 156

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
