#!/usr/bin/env python

#
# copyright Tom Goetz
#


import enum, logging


logger = logging.getLogger(__file__)


class Event(enum.Enum):
    race            = 1
    recreation      = 2
    special_event   = 3
    training        = 4
    transportation  = 5
    touring         = 6
    geocaching      = 7
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
    trail_running                   = 6
    street_running                  = 7
    track_running                   = 8
    walking                         = 9
    road_biking                     = 10
    indoor_cardio                   = 11
    strength_training               = 13
    casual_walking                  = 15
    speed_walking                   = 16
    top_level                       = 17
    treadmill_running               = 18
    cyclocross                      = 19
    downhill_biking                 = 20
    track_cycling                   = 21
    recumbent_cycling               = 22
    indoor_cycling                  = 25
    swimming                        = 26
    lap_swimming                    = 27
    open_water_swimming             = 28
    fitness_equipment               = 29
    elliptical                      = 30
    stair_climbing                  = 31
    indoor_rowing                   = 32
    snow_shoe                       = 36
    mountaineering                  = 37
    rowing                          = 39
    wind_kite_surfing               = 41
    horseback_riding                = 44
    driving_general                 = 49
    flying                          = 52
    paddling                        = 57
    whitewater_rafting_kayaking     = 60
    skating                         = 62
    inline_skating                  = 63
    resort_skiing_snowboarding      = 67
    backcountry_skiing_snowboarding = 68
    boating                         = 75
    sailing                         = 77
    cross_country_skiing            = 81
    stand_up_paddleboarding         = 87
    golf                            = 88
    bmx                             = 131
    hunting_fishing                 = 133
    surfing                         = 137
    wakeboarding                    = 138
    rock_climbing                   = 139
    hang_gliding                    = 140
    tennis                          = 142
    gravel_cycling                  = 143
    diving                          = 144
    yoga                            = 149
    floor_climbing                  = 150
    virtual_ride                    = 152
    virtual_run                     = 153
    obstacle_run                    = 154
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
