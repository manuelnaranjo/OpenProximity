"""
Some OpenProximity context variables that are some times
required
"""
import os
from django.conf import settings
try:
    from openproximity import version as opversion
except:
    opversion = 'ND'

def variables(requesst):
    return {
        'version': { 'current': opversion },
        'settings': {
            'logo': settings.OP2_LOGO,
            'debug': settings.OP2_DEBUG,
            'translate': settings.OP2_TRANSLATE,
            'twitter': settings.OP2_TWITTER
        }
    }
