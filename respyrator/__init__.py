##############################################################################
# For copyright and license notices, see LICENSE file in root directory
##############################################################################
from . import core

core = core.Core()
__version__ = core.version

from . import serial
from . import ui
