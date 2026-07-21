import os
import sys

_modules_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "modules")
if _modules_root not in sys.path:
    sys.path.insert(0, _modules_root)

from modules.argu_god.engine.expand import expand_topic
