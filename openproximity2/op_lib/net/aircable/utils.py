# -*- coding: utf-8 -*-
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
import const
import logging
import logging.handlers
import os, sys, time

def isAIRcable(address):
    return address[:8].upper() in const.AIRCABLE_MAC

import preset as settings

def getLogger(name="default"):
    if name in loggers:
        return loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.NOTSET)

    if name and name in settings.DEBUG_DISABLES:
        logging.getLogger("default").info("disabled")
        return logger

    logger.handlers = []

    #print name, clogger, clogger.level
    if name:
        logger.addHandler(clogger)

    if not flogger:
        logging.getLogger("default").warning(
            "Can't write to log file at %s" % flogger_file)
    else:
        logger.addHandler(flogger)

    loggers[name]=logger
    logging.getLogger("default").info("Added logger for %s" % name)
    return logger

if not hasattr(logging, "setup_done"):
    print "Doing logging base setup"
    logging.basicConfig()
    logging.setup_done = True
    logging.getLogger(None).addHandler(logging.NullHandler())

    clogger = logging.StreamHandler()
    clogger.setFormatter(logging.Formatter(settings.DEBUG_CONSOLE_FORMAT))
    clogger.setLevel(getattr(logging, settings.DEBUG_CONSOLE, logging.NOTSET))

    flogger = None
    flogger_file=None
    flogger_file = os.path.join(settings.DEBUG_PATH, settings.DEBUG_FILENAME)

    try:
        open(flogger_file, "w")
        size = 1024*1024*settings.DEBUG_MAXSIZE
        count = settings.DEBUG_COUNT
        flogger=logging.handlers.RotatingFileHandler(flogger_file, 
                                                     maxBytes=size,
                                                     backupCount=count)
        format=logging.Formatter(settings.DEBUG_FORMAT)
        flogger.setLevel(getattr(logging, settings.DEBUG_LEVEL, logging.NOTSET))
        flogger.setFormatter(format)
    except:
        flogger = None
    loggers={}
    getLogger(None).setLevel(logging.NOTSET)

def trace():
    try:
        #from pydbgr.api import debug as set_trace
        from pudb import set_trace
        import urwid
        def t(*args, **kwargs):
            pass
        urwid.raw_display.Screen.signal_init=t
        urwid.raw_display.Screen.signal_restore=t
    except Exception, err:
        logger.warning("Using non multithreaded pdb")
        from pdb import set_trace 
    return set_trace()

def register_debug_shell():
    ''' 
        a helper function that will allow to start pdb or pudb
        when CTRL-C is received
    '''
    if 'PDB' not in os.environ:
        return

    logger.debug("Registering PDB debugger")
    def signal_handler(signal, frame):
        trace()
    import signal
    signal.signal(signal.SIGINT, signal_handler)

register_debug_shell()

def get_subclass(object):
    for related in object._meta.get_all_related_objects():
        if type(object) in related.model._meta.get_parent_list():
            if hasattr(object,related.var_name):
                return get_subclass(getattr(object, related.var_name))
    return object

def get_subclasses(klass):
    out = [klass, ]
    if len(klass.__subclasses__()) > 0:
        for k in klass.__subclasses__():
            out.extend(get_subclasses(k))
    return out
