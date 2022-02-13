#!/usr/bin/env python3

"""A script that generated graphs for health data in a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from IPython.display import display
import ipyleaflet
import ipywidgets

from .config_manager import ConfigManager


logger = logging.getLogger()


class Map():
    """Display a map."""

    def __init__(self, center, width=None, height=None, zoom=None, fullscreen_widget=False):
        """Return a instance of a Map."""
        if width is None:
            width = ConfigManager.get_maps('width')
        if height is None:
            height = ConfigManager.get_maps('height')
        if zoom is None:
            zoom = 15
        layout = ipywidgets.Layout(width=f'{width}px', height=f'{height}px')
        self.map = ipyleaflet.Map(center=center, zoom=zoom, layout=layout)
        self.map.add_control(ipyleaflet.ScaleControl(position='bottomleft'))
        if fullscreen_widget:
            self.map.add_control(ipyleaflet.FullScreenControl())

    @classmethod
    def centroid(cls, points):
        """Return the centroid for a list of points."""
        return (sum([point[0] for point in points]) / len(points), sum([point[1] for point in points]) / len(points))

    def display(self):
        """Show the map."""
        display(self.map)


class ActivityMap(Map):
    """Display a map of an activity."""

    def __init__(self, records, laps=[], width=None, height=None, fullscreen_widget=False):
        """Return a instance of a ActivityMap."""
        locations = [[record.position_lat, record.position_long] for record in records if record.position_lat is not None and record.position_long is not None]
        lap_locations = [[lap.start_lat, lap.start_long] for lap in laps if lap.start_lat is not None and lap.start_long is not None]
        super().__init__(self.centroid(locations), width=width, height=height, fullscreen_widget=fullscreen_widget)
        ant_path = ipyleaflet.AntPath(locations=locations, dash_array=[1, 10], delay=2000, color='#7590ba', pulse_color='#3f6fba')
        self.map.add_layer(ant_path)
        start_marker = ipyleaflet.Marker(location=locations[0], title='start', draggable=False)
        self.map.add_layer(start_marker)
        stop_marker = ipyleaflet.Marker(location=locations[-1], title='stop', draggable=False)
        for lap_num, lap_location in enumerate(lap_locations):
            lap_marker = ipyleaflet.Marker(location=lap_location, title=f'lap {lap_num}', draggable=False)
            self.map.add_layer(lap_marker)
        self.map.add_layer(stop_marker)
