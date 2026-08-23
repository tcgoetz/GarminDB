"""Objects representing golf data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey

import idbutils
from .garmin_db import GarminDb


class GolfScorecard(GarminDb.Base, idbutils.DbObject):
    """Class representing a Garmin golf scorecard."""

    __tablename__ = 'golf_scorecards'

    db = GarminDb
    table_version = 1

    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    course_name = Column(String)
    strokes = Column(Integer)
    score_without_handicap = Column(Integer)
    holes_completed = Column(Integer)
    round_type = Column(String)
    score_type = Column(String)
    handicapped_strokes = Column(Integer)


class GolfHole(GarminDb.Base, idbutils.DbObject):
    """Class representing a Garmin golf hole within a scorecard."""

    __tablename__ = 'golf_holes'

    db = GarminDb
    table_version = 1

    id = Column(Integer, primary_key=True, autoincrement=True)
    scorecard_id = Column(Integer, ForeignKey('golf_scorecards.id'), nullable=False)
    hole_number = Column(Integer)
    par = Column(Integer)
    strokes = Column(Integer)
    putts = Column(Integer)


class GolfShot(GarminDb.Base, idbutils.DbObject):
    """Class representing a Garmin golf shot."""

    __tablename__ = 'golf_shots'

    db = GarminDb
    table_version = 1

    id = Column(Integer, primary_key=True, autoincrement=True)
    scorecard_id = Column(Integer, ForeignKey('golf_scorecards.id'), nullable=False)
    hole_number = Column(Integer)
    shot_number = Column(Integer)
    club_name = Column(String)
    distance_meters = Column(Float)
    shot_type = Column(String)
