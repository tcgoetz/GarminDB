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
        if len(points) and len(points):
            return (sum([point[0] for point in points]) / len(points), sum([point[1] for point in points]) / len(points))

    def display(self):
        """Show the map."""
        display(self.map)


class ColoredPin(ipyleaflet.Icon):
    """Base class for colored map pins."""

    def __init__(self, color):
        """Return a new instance of a colored map pin."""
        super().__init__(
            icon_url=f'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{color}.png',
            shadow_url='https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            icon_size=(25, 41),
            shadow_size=(41, 41),
            icon_anchor=(12, 41),
            popup_anchor=(1, -34)
        )


green_pin = ColoredPin('green')
red_pin = ColoredPin('red')
blue_pin = ColoredPin('blue')


class ActivityMap(Map):
    """Display a map of an activity."""

    def __init__(self, records, laps=[], width=None, height=None, fullscreen_widget=False):
        """Return a instance of a ActivityMap."""
        locations = [[record.position_lat, record.position_long] for record in records if record.position_lat is not None and record.position_long is not None]
        lap_locations = [[lap.stop_lat, lap.stop_long] for lap in laps if lap.start_lat is not None and lap.start_long is not None]
        super().__init__(self.centroid(locations), width=width, height=height, fullscreen_widget=fullscreen_widget)
        ant_path = ipyleaflet.AntPath(locations=locations, dash_array=[1, 10], delay=2000, color='#7590ba', pulse_color='#3f6fba')
        self.map.add_layer(ant_path)
        for lap_num, lap_location in enumerate(lap_locations, start=1):
            lap_marker = ipyleaflet.Marker(location=lap_location, title=f'lap {lap_num}', draggable=False, icon=blue_pin)
            self.map.add_layer(lap_marker)
        start_marker = ipyleaflet.Marker(location=locations[0], title='start', draggable=False, icon=green_pin)
        self.map.add_layer(start_marker)
        stop_marker = ipyleaflet.Marker(location=locations[-1], title='stop', draggable=False, icon=red_pin)
        self.map.add_layer(stop_marker)
