"""Objects for importing Garmin golf data from Garmin Connect downloads."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import dateutil.parser

from idbutils import JsonFileProcessor

from .garmindb import GarminDb, GolfScorecard, GolfHole, GolfShot

logger = logging.getLogger(__file__)


class GarminGolfScorecardData(JsonFileProcessor):
    """Class for importing Garmin golf data from JSON formatted Garmin Connect downloads."""

    def __init__(self, db_params, input_dir, latest, debug):
        super().__init__(r'scorecard_summary_\d*\.json', input_dir=input_dir, latest=latest, debug=debug)
        self.garmin_db = GarminDb(db_params, self.debug - 1)
        self.conversions = {}

    def _process_json(self, json_data):
        with self.garmin_db.managed_session() as session:
            start_time = dateutil.parser.parse(self._get_field(json_data, 'startTime'), ignoretz=True) if json_data.get('startTime') else None
            end_time = dateutil.parser.parse(self._get_field(json_data, 'endTime'), ignoretz=True) if json_data.get('endTime') else None

            scorecard = {
                'id': json_data.get('id'),
                'start_time': start_time,
                'end_time': end_time,
                'course_name': self._get_field(json_data, 'courseName'),
                'strokes': self._get_field(json_data, 'strokes', int),
                'score_without_handicap': self._get_field(json_data, 'scoreWithoutHandicap', int),
                'holes_completed': self._get_field(json_data, 'holesCompleted', int),
                'round_type': self._get_field(json_data, 'roundType'),
                'score_type': self._get_field(json_data, 'scoreType'),
                'handicapped_strokes': self._get_field(json_data, 'handicappedStrokes', int)
            }
            GolfScorecard.s_insert_or_update(session, scorecard, ignore_none=True)
            return 1


class GarminGolfScorecardDetailData(JsonFileProcessor):
    def __init__(self, db_params, input_dir, latest, debug):
        super().__init__(r'scorecard_detail_\d*\.json', input_dir=input_dir, latest=latest, debug=debug)
        self.garmin_db = GarminDb(db_params, self.debug - 1)
        self.conversions = {}

    def _process_json(self, json_data):
        with self.garmin_db.managed_session() as session:
            scorecard_id = json_data.get('scorecardId') or json_data.get('id')
            if not scorecard_id:
                return 0
            holes = json_data.get('holes', [])
            count = 0
            for hole in holes:
                hole_data = {
                    'scorecard_id': scorecard_id,
                    'hole_number': self._get_field(hole, 'holeNumber', int),
                    'par': self._get_field(hole, 'par', int),
                    'strokes': self._get_field(hole, 'strokes', int),
                    'putts': self._get_field(hole, 'putts', int)
                }
                GolfHole.s_insert_or_update(session, hole_data, ignore_none=True)
                count += 1
            return count


class GarminGolfShotData(JsonFileProcessor):
    def __init__(self, db_params, input_dir, latest, debug):
        super().__init__(r'scorecard_shot_\d*\.json', input_dir=input_dir, latest=latest, debug=debug)
        self.garmin_db = GarminDb(db_params, self.debug - 1)
        self.conversions = {}

    def _process_json(self, json_data):
        with self.garmin_db.managed_session() as session:
            scorecard_id = json_data.get('scorecardId')
            holes = json_data.get('holeShots', json_data.get('holes', []))
            if not holes and type(json_data) is list:
                holes = json_data

            count = 0
            for hole in holes:
                hole_num = hole.get('holeNumber')
                if not hole_num:
                    continue
                shots = hole.get('shots', [])
                for shot in shots:
                    shot_data = {
                        'id': shot.get('id'),
                        'scorecard_id': shot.get('scorecardId', hole.get('scorecardId', scorecard_id)),
                        'hole_number': hole_num,
                        'shot_number': self._get_field(shot, 'shotOrder', int),
                        'club_name': self._get_field(shot, 'clubName'),
                        'distance_meters': self._get_field(shot, 'meters', float) or self._get_field(shot, 'distanceInMeters', float),
                        'shot_type': self._get_field(shot, 'shotType')
                    }
                    if not shot_data['scorecard_id']:
                        continue
                    GolfShot.s_insert_or_update(session, shot_data, ignore_none=True)
                    count += 1
            return count
