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

    def __init__(self, center, width=None, height=None, zoom=None):
        """Return a instance of a Map."""
        if width is None:
            width = ConfigManager.get_maps('width')
        if height is None:
            height = ConfigManager.get_maps('height')
        if zoom is None:
            zoom = 15
        layout = ipywidgets.Layout(width=f'{width}px', height=f'{height}px')
        self.map = ipyleaflet.Map(center=center, zoom=zoom, layout=layout)

    def display(self):
        """Show the map."""
        display(self.map)


class ActivityMap(Map):
    """Display a map of an activity."""

    def __init__(self, records, width=None, height=None):
        """Return a instance of a ActivityMap."""
        locations = [[record.position_lat, record.position_long] for record in records if record.position_lat is not None and record.position_long is not None]
        centroid = (sum([location[0] for location in locations]) / len(locations), sum([location[1] for location in locations]) / len(locations))
        super().__init__(centroid, width, height)
        ant_path = ipyleaflet.AntPath(locations=locations, dash_array=[1, 10], delay=2000, color='#7590ba', pulse_color='#3f6fba')
        self.map.add_layer(ant_path)
        start_marker = ipyleaflet.Marker(location=locations[0], title='start', draggable=False)
        self.map.add_layer(start_marker)
        stop_marker = ipyleaflet.Marker(location=locations[-1], title='stop', draggable=False)
        self.map.add_layer(stop_marker)