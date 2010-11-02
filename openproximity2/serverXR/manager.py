#!/usr/bin/python
#
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
#
# -*- coding: utf-8 -*-
import dbus, dbus.glib, gobject, select
import os, sys, errno
import rpyc

from rpyc import async
from net.aircable import autoreload
from net.aircable.openproximity.pluginsystem import pluginsystem
from net.aircable.utils import logger, logmain

if __name__=='__main__':
    logmain("serverXR/manager.py")

server = None
manager = None
bus = None
loop = None

def poll(fd, condition):
    '''
    This function gets called whenever there's data waiting in the incomming 
    socket, so we can flush the data from the server.
    '''
    try:
	server.poll()
	return True
    except EOFError, eof:
	logger.error("EOF while polling %s" % eof)
        logger.exception(eof)
        stop()
        return False 
    except Exception, err:
	logger.error("error during poll %s" % err)
	logger.exception(err)
    return True

def stop():
    '''
    Safe stop function
    '''
    global manager
    from uploader import UploadManager
    if getattr(manager, 'exposed_stop', None):
        manager.exposed_stop()
    loop.quit()

def handle_name_owner_changed(own, old, new):
    '''
    Will get called whenever a name owner changes in dbus.
    If the change is with the BlueZ name (either it started or ended) then
    we stop the rpc client so it restarts.
    '''
    if own.startswith('org.bluez'):
        if new is None or len(str(new))==0:
            logger.info( "bluez has gone down, time to get out")
        else:
            logger.info( "bluez started, time to restart")
        stop()

def handle_adapter_added_or_removed(path, signal):
    '''
    When ever a dongle is added or removed this function gets called, so we can
    restart the rpc client.
    '''
    logger.info("bluez.%s: %s" % (signal, path))
    stop()

def init():
    '''
    Gets called from inside the gobject loop once dbus is accessible so we can
    complete the init process.
    '''
    global manager, bus, loop, server
    
    logger.info("init")
    
    type__ = sys.argv[3].lower()

    # get the list of connected dongles
    a=list()
    for b in manager.manager.ListAdapters():
        obj = bus.get_object('org.bluez', b)
        adapter = dbus.Interface(obj, 'org.bluez.Adapter')
        a.append(str(adapter.GetProperties()['Address']))
    logger.info("Connected dongles: %s" % a)

    # do the remote registration.
    register={
	'scanner': async(server.root.scanner_register),
	'uploader': async(server.root.uploader_register),
    }.get(type__, async(server.root.generic_register))

    register(
        remote_quit=stop, 
        client=manager, 
        dongles=a, 
    )
    logger.info("exiting init")

    # stupid way to make rpyc do something
    str(server.root)

    return False

def run(server_, port, type_):
    '''
	Will get called from a child process once the autoreload system is ready
	everything will be setup so the rpc client can work.
    '''
    global server, manager, bus, loop
    
    loop=gobject.MainLoop()
    
    # first connect to the server, we can't do much without it
    try:
        server = rpyc.connect(server_, int(port))
    except:
        import time
        logger.info("server is not running")
        time.sleep(10)
        autoreload.RELOAD = True
        sys.exit(3)

    # now try to get into dbus and init gobject
    bus=dbus.SystemBus()
    gobject.threads_init()
    dbus.glib.init_threads()

    # register for a few signals
    bus.add_signal_receiver(
        handle_name_owner_changed,
        'NameOwnerChanged',
        'org.freedesktop.DBus',
        'org.freedesktop.DBus',
        '/org/freedesktop/DBus'
    )

    bus.add_signal_receiver(
        handle_adapter_added_or_removed,
        signal_name='AdapterAdded',
        dbus_interface='org.bluez.Manager',
        member_keyword='signal' 
    )

    bus.add_signal_receiver(
        handle_adapter_added_or_removed,
        signal_name='AdapterRemoved',
        dbus_interface='org.bluez.Manager',
        member_keyword='signal'
    )

    # create the manager and register for init
    try:
        if type_ == 'scanner':
            from scanner import ScanManager
            logger.info("init scanner")
            manager = ScanManager(bus, rpc=server)
        elif type_ == 'uploader':
            logger.info("init uploader")
            from uploader import UploadManager
            manager = UploadManager(bus, rpc=server, loop=loop)
        else:
            for i in pluginsystem.get_plugins('serverxr'):
                if type_==i.provides['serverxr_type']:
                    logger.info("init %s" % i.provides['serverxr_type'])
                    module = __import__("%s.serverxr" % i.name, fromlist=[i.provides['serverxr_manager'],])
                    klass = getattr(module, i.provides['serverxr_manager'])
                    manager = klass (bus, rpc=server)
                    break
        if manager is None:
            raise Exception ("Not valid type")
        gobject.timeout_add(100, init) # delay initialization 'til loop is running
    except dbus.DBusException, err:
        logger.info("bluez isn't ready, delaying init")

    # start our loop and setup ping
    flags = gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP
    gobject.io_add_watch(server.fileno(), flags, poll)
    # give control to the mainloop
    loop.run()

    # if we get here by any how then it's time to restart
    autoreload.RELOAD = True

if __name__ == '__main__':
    # setup autoreload
    if autoreload.isParent() and len(sys.argv) < 4:
        print "usage: %s server-ip port type" % sys.argv[0]
        sys.exit(0)

    from django.core.management import execute_manager, setup_environ
    import settings
    setup_environ(settings)

    # get a list of valid modes
    valid_modes=['scanner', 'uploader']

    valid_modes.extend(
        [ i.provides['serverxr_type'] 
            for i in pluginsystem.get_plugins('serverxr') ] )

    if sys.argv[3] not in valid_modes:
        print "not valid type, you can use any of", valid_modes
        sys.exit(0)

    # register for autoreload
    autoreload.main(run, tuple(sys.argv[1:4]),{})

