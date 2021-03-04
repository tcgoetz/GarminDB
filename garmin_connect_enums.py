"""Enums representing Garmin Connect data types."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import enum
import logging

import Fit


logger = logging.getLogger(__file__)


class Event(enum.Enum):
    """Garmin Connect event types enum."""

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
        """Create a Event enum instance from Garmin Connect JSON data."""
        json_event = json_data['eventType']
        try:
            return cls(json_event['typeId'])
        except ValueError:
            logger.error("Unknown event type: %r", json_event)
            raise


class Sport(enum.Enum):
    """Garmin Connect sport types enum."""

    running                                 = 1
    cycling                                 = 2
    hiking                                  = 3
    other                                   = 4
    mountain_biking                         = 5
    trail_running                           = 6
    street_running                          = 7
    track_running                           = 8
    walking                                 = 9
    road_biking                             = 10
    indoor_cardio                           = 11
    strength_training                       = 13
    casual_walking                          = 15
    speed_walking                           = 16
    top_level                               = 17
    treadmill_running                       = 18
    cyclocross                              = 19
    downhill_biking                         = 20
    track_cycling                           = 21
    recumbent_cycling                       = 22
    indoor_cycling                          = 25
    swimming                                = 26
    lap_swimming                            = 27
    open_water_swimming                     = 28
    fitness_equipment                       = 29
    elliptical                              = 30
    stair_climbing                          = 31
    indoor_rowing                           = 32
    snow_shoe                               = 36
    mountaineering                          = 37
    rowing                                  = 39
    wind_kite_surfing                       = 41
    horseback_riding                        = 44
    driving_general                         = 49
    flying                                  = 52
    paddling                                = 57
    whitewater_rafting_kayaking             = 60
    skating                                 = 62
    inline_skating                          = 63
    resort_skiing_snowboarding              = 67
    backcountry_skiing_snowboarding         = 68
    boating                                 = 75
    sailing                                 = 77
    cross_country_skiing                    = 81
    stand_up_paddleboarding                 = 87
    golf                                    = 88
    bmx                                     = 131
    hunting_fishing                         = 133
    surfing                                 = 137
    wakeboarding                            = 138
    rock_climbing                           = 139
    hang_gliding                            = 140
    tennis                                  = 142
    gravel_cycling                          = 143
    diving                                  = 144
    yoga                                    = 149
    floor_climbing                          = 150
    virtual_ride                            = 152
    virtual_run                             = 153
    obstacle_run                            = 154
    indoor_running                          = 156
    safety                                  = 157
    assistance                              = 158
    incident_detected                       = 159
    ccr_diving                              = 161
    auto_racing                             = 162
    yoga_gym                                = 163
    breathwork                              = 164
    winter_sports                           = 165
    snow_shoe_ws                            = 167
    skating_ws                              = 168
    backcountry_skiing_snowboarding_ws      = 169
    skate_skiing_ws                         = 170
    cross_country_skiing_ws                 = 171
    resort_skiing_snowboarding_ws           = 172

    @classmethod
    def __activity_from_json(cls, json_data):
        return json_data['activityType']

    @classmethod
    def __activity_from_details_json(cls, json_data):
        return json_data['activityTypeDTO']

    @classmethod
    def __sport_from_json(cls, json_activity):
        return json_activity['parentTypeId']

    @classmethod
    def __subsport_from_json(cls, json_activity):
        return json_activity['typeId']

    @classmethod
    def from_json(cls, json_data):
        """Create a Sport enum instance from Garmin Connect JSON data."""
        json_activity = cls.__activity_from_json(json_data)
        try:
            return Sport(cls.__sport_from_json(json_activity))
        except ValueError:
            logger.error("Unknown sport type: %r", json_activity)

    @classmethod
    def from_details_json(cls, json_data):
        """Create a Sport enum instance from Garmin Connect JSON details data."""
        json_activity = cls.__activity_from_details_json(json_data)
        try:
            return Sport(cls.__sport_from_json(json_activity))
        except ValueError:
            logger.error("Unknown sport type: %r", json_activity)

    @classmethod
    def subsport_from_json(cls, json_data):
        """Create a Sport enum instance from Garmin Connect subsport JSON data."""
        json_activity = cls.__activity_from_json(json_data)
        try:
            return Sport(cls.__subsport_from_json(json_activity))
        except ValueError:
            logger.error("Unknown subsport type: %r", json_activity)

    @classmethod
    def subsport_from_details_json(cls, json_data):
        """Create a Sport enum instance from Garmin Connect subsport JSON details data."""
        json_activity = cls.__activity_from_details_json(json_data)
        try:
            return Sport(cls.__subsport_from_json(json_activity))
        except ValueError:
            logger.error("Unknown subsport type: %r", json_activity)


def convert_gc_sport_to_fit(gc_sport, gc_sub_sport):
    """Convert sport and subsport values from Garmin Connect to Fit values."""
    remap_gc_sub_sport_to_fit = {
        Sport.mountain_biking                         : Fit.SubSport.mountain,
        Sport.trail_running                           : Fit.SubSport.trail,
        Sport.street_running                          : Fit.SubSport.street,
        Sport.track_running                           : Fit.SubSport.track,
        Sport.road_biking                             : Fit.SubSport.road,
        Sport.casual_walking                          : Fit.SubSport.casual_walking,
        Sport.speed_walking                           : Fit.SubSport.speed_walking,
        Sport.treadmill_running                       : Fit.SubSport.treadmill,
        Sport.downhill_biking                         : Fit.SubSport.downhill,
        Sport.track_cycling                           : Fit.SubSport.track_cycling,
        Sport.recumbent_cycling                       : Fit.SubSport.recumbent,
        Sport.indoor_cycling                          : Fit.SubSport.indoor_cycling,
        Sport.strength_training                       : Fit.SubSport.strength_training,
        Sport.cyclocross                              : Fit.SubSport.cyclocross,
        Sport.lap_swimming                            : Fit.SubSport.lap_swimming,
        Sport.open_water_swimming                     : Fit.SubSport.open_water,
        Sport.elliptical                              : Fit.SubSport.elliptical,
        Sport.stair_climbing                          : Fit.SubSport.stair_climbing,
        Sport.indoor_rowing                           : Fit.SubSport.indoor_rowing,
        Sport.bmx                                     : Fit.SubSport.bmx,
        Sport.gravel_cycling                          : Fit.SubSport.gravel_cycling,
        Sport.yoga                                    : Fit.SubSport.yoga,
        Sport.obstacle_run                            : Fit.SubSport.obstacle,
        Sport.indoor_running                          : Fit.SubSport.indoor_running,
        Sport.yoga_gym                                : Sport.yoga_gym
    }
    remap_winter_sports = {
        Sport.snow_shoe_ws                            : Fit.Sport.snowshoeing,
        Sport.skating_ws                              : Fit.Sport.ice_skating,
        Sport.backcountry_skiing_snowboarding_ws      : Sport.backcountry_skiing_snowboarding,
        Sport.skate_skiing_ws                         : Sport.skate_skiing_ws,
        Sport.cross_country_skiing_ws                 : Fit.Sport.cross_country_skiing,
        Sport.resort_skiing_snowboarding_ws           : Sport.resort_skiing_snowboarding
    }
    remap_gc_sport_to_fit = {
        Sport.running                                 : Fit.Sport.running,
        Sport.cycling                                 : Fit.Sport.cycling,
        Sport.hiking                                  : Fit.Sport.hiking,
        Sport.walking                                 : Fit.Sport.walking,
        Sport.indoor_cardio                           : Sport.indoor_cardio,
        Sport.swimming                                : Fit.Sport.swimming,
        Sport.fitness_equipment                       : Fit.Sport.fitness_equipment,
        Sport.snow_shoe                               : Fit.Sport.snowshoeing,
        Sport.mountaineering                          : Fit.Sport.mountaineering,
        Sport.rowing                                  : Fit.Sport.rowing,
        Sport.wind_kite_surfing                       : Fit.Sport.kitesurfing,
        Sport.horseback_riding                        : Fit.Sport.horseback_riding,
        Sport.driving_general                         : Fit.Sport.driving,
        Sport.flying                                  : Fit.Sport.flying,
        Sport.paddling                                : Fit.Sport.paddling,
        Sport.whitewater_rafting_kayaking             : Sport.whitewater_rafting_kayaking,
        Sport.skating                                 : Fit.Sport.ice_skating,
        Sport.inline_skating                          : Fit.Sport.inline_skating,
        Sport.resort_skiing_snowboarding              : Sport.resort_skiing_snowboarding,
        Sport.backcountry_skiing_snowboarding         : Sport.backcountry_skiing_snowboarding,
        Sport.boating                                 : Fit.Sport.boating,
        Sport.sailing                                 : Fit.Sport.sailing,
        Sport.cross_country_skiing                    : Fit.Sport.cross_country_skiing,
        Sport.stand_up_paddleboarding                 : Fit.Sport.stand_up_paddleboarding,
        Sport.golf                                    : Fit.Sport.golf,
        Sport.hunting_fishing                         : Sport.hunting_fishing,
        Sport.surfing                                 : Fit.Sport.surfing,
        Sport.wakeboarding                            : Fit.Sport.wakeboarding,
        Sport.rock_climbing                           : Fit.Sport.rock_climbing,
        Sport.hang_gliding                            : Fit.Sport.hang_gliding,
        Sport.tennis                                  : Fit.Sport.tennis,
        Sport.diving                                  : Sport.diving,
        Sport.floor_climbing                          : Fit.Sport.floor_climbing,
        Sport.virtual_ride                            : Sport.virtual_ride,
        Sport.virtual_run                             : Sport.virtual_run,
        Sport.safety                                  : Sport.safety,
        Sport.assistance                              : Sport.assistance,
        Sport.incident_detected                       : Sport.incident_detected,
        Sport.ccr_diving                              : Sport.ccr_diving,
        Sport.auto_racing                             : Sport.auto_racing,
        Sport.breathwork                              : Sport.breathwork,
        Sport.other                                   : Sport.other,
    }
    special_remaps = {
        Sport.other                                   : remap_gc_sport_to_fit.get(gc_sub_sport),
        Sport.top_level                               : remap_gc_sport_to_fit.get(gc_sub_sport),
        Sport.winter_sports                           : remap_winter_sports.get(gc_sub_sport),
    }
    if gc_sport in special_remaps.keys():
        return (special_remaps[gc_sport], Fit.Sport.generic)
    return (remap_gc_sport_to_fit.get(gc_sport), remap_gc_sub_sport_to_fit.get(gc_sub_sport))


def get_details_sport(json_data):
    """Get the sport and sub-sport and convert to Fit values if possible."""
    sport = Sport.from_details_json(json_data)
    sub_sport = Sport.subsport_from_details_json(json_data)
    return convert_gc_sport_to_fit(sport, sub_sport)


def get_summary_sport(json_data):
    """Get the sport and sub-sport and convert to Fit values if possible."""
    sport = Sport.from_json(json_data)
    sub_sport = Sport.subsport_from_json(json_data)
    return convert_gc_sport_to_fit(sport, sub_sport)
