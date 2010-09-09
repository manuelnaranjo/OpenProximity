from django import template
from net.aircable.openproximity.pluginsystem import pluginsystem

register=template.Library()

def getCamera():
    try:
        return __import__('camera', level=0)
    except:	
        return __import__('plugins.camera', fromlist=['__version__', 'find_plugins'], level=0)
camera=getCamera()

def camera_version():
    return camera.__version__

register.simple_tag(camera_version)
