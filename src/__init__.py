__version__ = "1.1.dev"

import os

# Useful constants
PACKAGEDIR = os.path.abspath(os.path.dirname(__file__))

# Try relative import (when used as installed package)
# Fall back to absolute import (when imported directly from source)
try:
    from .kpub import *
except ImportError:
    from kpub import *
