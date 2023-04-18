import imp

from . import test_panel
from . import lib_preferences

imp.reload(lib_preferences)

classes = [
    test_panel.MyPanel,
    
]