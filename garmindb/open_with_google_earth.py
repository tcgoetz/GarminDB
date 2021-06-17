"""Open a TCX file in Google Earth."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

from idbutils import OpenWithApp


class OpenWithGoogleEarth(OpenWithApp):
    """Class that opens a file with an application regardsless of platform."""

    @classmethod
    def _open_on_darwin(cls, filename):
        """Open a file with MacOS application."""
        # cls.open_on_darwin('Google Earth Pro.app', filename)
        cls.open_on_darwin_with_applescript('Google Earth Pro', f'open POSIX file "{filename}"')
