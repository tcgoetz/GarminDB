"""Test config handling."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import unittest
import logging
import sys

import fitfile
import idbutils
import tcxfile

sys.path.append('..')
from fitfile import version_string as fit_version_string
from idbutils import version_string as utilities_version_string
from tcxfile import version_string as tcx_version_string


root_logger = logging.getLogger()
handler = logging.FileHandler('copy.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestModuleVersions(unittest.TestCase):
    """Class for testing imported module versions match the source tree."""

    def test_versions(self):
        print(f"fitfile version {fitfile.__version__}")
        self.assertEqual(fitfile.__version__, fit_version_string(), f'Fit version actual {fitfile.__version__} expected {fit_version_string()}')
        print(f"idbutils version {idbutils.__version__}")
        self.assertEqual(idbutils.__version__, utilities_version_string(), f'Utilities version actual {idbutils.__version__} expected {utilities_version_string()}')
        print(f"tcxfile version {tcxfile.__version__}")
        self.assertEqual(tcxfile.__version__, tcx_version_string(), f'Tcx version actual {tcxfile.__version__} expected {tcx_version_string()}')


if __name__ == '__main__':
    unittest.main(verbosity=2)