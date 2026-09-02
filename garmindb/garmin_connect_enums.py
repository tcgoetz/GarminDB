"""Enums representing Garmin Connect data types."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import enum
import logging

import fitfile


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
    indoor_climbing                         = 173
    bouldering                              = 174
    e_bike_mountain                         = 175
    e_bike_fitness                          = 176
    onshore_grinding                        = 178
    offshore_grinding                       = 179
    hiit                                    = 180
    ultra_run                               = 181
    e_sport                                 = 182
    windsurfing                             = 183
    kiteboarding                            = 184
    motorcycling_v2                         = 185
    motocross_v2                            = 186
    atv_v2                                  = 187
    transition_v2                           = 189
    swimToBikeTransition_v2                 = 190
    bikeToRunTransition_v2                  = 191
    runToBikeTransition_v2                  = 192
    hunting                                 = 193
    fishing                                 = 194
    whitewater_rafting                      = 195
    kayaking                                = 196
    hand_cycling                            = 197
    indoor_hand_cycling                     = 198
    para_sports                             = 199
    wheelchair_push_run                     = 200
    wheelchair_push_walk                    = 201
    meditation                              = 202
    backcountry_skiing                      = 203
    backcountry_snowboarding                = 204
    disc_golf                               = 205
    team_sports                             = 206
    cricket                                 = 207
    rugby                                   = 208
    ice_hockey                              = 209
    field_hockey                            = 210
    lacrosse                                = 211
    volleyball                              = 212
    ultimate_disc                           = 213
    softball                                = 214
    soccer                                  = 215
    american_football                       = 216
    basketball                              = 217
    baseball                                = 218
    racket_sports                           = 219
    table_tennis                            = 220
    platform_tennis                         = 221
    racquetball                             = 222
    squash                                  = 223
    badminton                               = 224
    pickleball                              = 225
    paddelball                              = 226
    tennis_v2                               = 227
    water_sports                            = 228
    boating_v2                              = 229
    fishing_v2                              = 230
    kayaking_v2                             = 231
    kiteboarding_v2                         = 232
    offshore_grinding_v2                    = 233
    onshore_grinding_v2                     = 234
    paddling_v2                             = 235
    whitewater_rafting_v2                   = 236
    rowing_v2                               = 237
    stand_up_paddleboarding_v2              = 239
    surfing_v2                              = 240
    water_tubing                            = 241
    windsurfing_v2                          = 242
    wakeboarding_v2                         = 243
    wakesurfing                             = 244
    waterskiing                             = 245
    boxing                                  = 246
    archery                                 = 247
    mixed_martial_arts                      = 248
    overland                                = 249
    snorkeling                              = 250
    resort_skiing                           = 251
    resort_snowboarding                     = 252
    dance                                   = 253
    jump_rope                               = 254

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
        Sport.mountain_biking                       : fitfile.fields.SubSport.mountain,
        Sport.trail_running                         : fitfile.fields.SubSport.trail,
        Sport.street_running                        : fitfile.fields.SubSport.street,
        Sport.track_running                         : fitfile.fields.SubSport.track,
        Sport.road_biking                           : fitfile.fields.SubSport.road,
        Sport.casual_walking                        : fitfile.fields.SubSport.casual_walking,
        Sport.speed_walking                         : fitfile.fields.SubSport.speed_walking,
        Sport.treadmill_running                     : fitfile.fields.SubSport.treadmill,
        Sport.downhill_biking                       : fitfile.fields.SubSport.downhill,
        Sport.track_cycling                         : fitfile.fields.SubSport.track_cycling,
        Sport.recumbent_cycling                     : fitfile.fields.SubSport.recumbent,
        Sport.indoor_cycling                        : fitfile.fields.SubSport.indoor_cycling,
        Sport.strength_training                     : fitfile.fields.SubSport.strength_training,
        Sport.cyclocross                            : fitfile.fields.SubSport.cyclocross,
        Sport.indoor_cardio                         : fitfile.fields.SubSport.cardio_training,
        Sport.lap_swimming                          : fitfile.fields.SubSport.lap_swimming,
        Sport.open_water_swimming                   : fitfile.fields.SubSport.open_water,
        Sport.elliptical                            : fitfile.fields.SubSport.elliptical,
        Sport.stair_climbing                        : fitfile.fields.SubSport.stair_climbing,
        Sport.indoor_rowing                         : fitfile.fields.SubSport.indoor_rowing,
        Sport.bmx                                   : fitfile.fields.SubSport.bmx,
        Sport.gravel_cycling                        : fitfile.fields.SubSport.gravel_cycling,
        Sport.yoga                                  : fitfile.fields.SubSport.yoga,
        Sport.obstacle_run                          : fitfile.fields.SubSport.obstacle,
        Sport.indoor_running                        : fitfile.fields.SubSport.indoor_running,
        Sport.indoor_climbing                       : fitfile.fields.SubSport.indoor_climbing,
        Sport.bouldering                            : fitfile.fields.SubSport.bouldering

    }
    remap_winter_sports = {
        Sport.snow_shoe_ws                            : fitfile.fields.Sport.snowshoeing,
        Sport.skating_ws                              : fitfile.fields.Sport.ice_skating,
        Sport.cross_country_skiing_ws                 : fitfile.fields.Sport.cross_country_skiing,
    }
    remap_gc_sport_to_fit = {
        Sport.running                                 : fitfile.fields.Sport.running,
        Sport.cycling                                 : fitfile.fields.Sport.cycling,
        Sport.hiking                                  : fitfile.fields.Sport.hiking,
        Sport.walking                                 : fitfile.fields.Sport.walking,
        Sport.swimming                                : fitfile.fields.Sport.swimming,
        Sport.fitness_equipment                       : fitfile.fields.Sport.fitness_equipment,
        Sport.snow_shoe                               : fitfile.fields.Sport.snowshoeing,
        Sport.mountaineering                          : fitfile.fields.Sport.mountaineering,
        Sport.rowing                                  : fitfile.fields.Sport.rowing,
        Sport.wind_kite_surfing                       : fitfile.fields.Sport.kitesurfing,
        Sport.horseback_riding                        : fitfile.fields.Sport.horseback_riding,
        Sport.driving_general                         : fitfile.fields.Sport.driving,
        Sport.flying                                  : fitfile.fields.Sport.flying,
        Sport.paddling                                : fitfile.fields.Sport.paddling,
        Sport.skating                                 : fitfile.fields.Sport.ice_skating,
        Sport.inline_skating                          : fitfile.fields.Sport.inline_skating,
        Sport.boating                                 : fitfile.fields.Sport.boating,
        Sport.sailing                                 : fitfile.fields.Sport.sailing,
        Sport.cross_country_skiing                    : fitfile.fields.Sport.cross_country_skiing,
        Sport.stand_up_paddleboarding                 : fitfile.fields.Sport.stand_up_paddleboarding,
        Sport.golf                                    : fitfile.fields.Sport.golf,
        Sport.surfing                                 : fitfile.fields.Sport.surfing,
        Sport.wakeboarding                            : fitfile.fields.Sport.wakeboarding,
        Sport.rock_climbing                           : fitfile.fields.Sport.rock_climbing,
        Sport.hang_gliding                            : fitfile.fields.Sport.hang_gliding,
        Sport.tennis                                  : fitfile.fields.Sport.tennis,
        Sport.floor_climbing                          : fitfile.fields.Sport.floor_climbing,
        Sport.windsurfing                             : fitfile.fields.Sport.windsurfing,
        Sport.kiteboarding                            : fitfile.fields.Sport.kitesurfing,
        Sport.hunting                                 : fitfile.fields.Sport.hunting,
        Sport.fishing                                 : fitfile.fields.Sport.fishing,
        Sport.whitewater_rafting                      : fitfile.fields.Sport.rafting,
        Sport.kayaking                                : fitfile.fields.Sport.kayaking,
        Sport.stand_up_paddleboarding_v2              : fitfile.fields.Sport.stand_up_paddleboarding
    }
    special_remaps = {
        Sport.other                                   : remap_gc_sport_to_fit.get(gc_sub_sport, gc_sub_sport),
        Sport.top_level                               : remap_gc_sport_to_fit.get(gc_sub_sport, gc_sub_sport),
        Sport.winter_sports                           : remap_winter_sports.get(gc_sub_sport, gc_sub_sport)
    }
    if gc_sport in special_remaps.keys():
        return (special_remaps[gc_sport], fitfile.fields.Sport.generic)
    return (remap_gc_sport_to_fit.get(gc_sport, gc_sport), remap_gc_sub_sport_to_fit.get(gc_sub_sport, gc_sub_sport))


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
