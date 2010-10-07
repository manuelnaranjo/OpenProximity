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
    global manager
    from uploader import UploadManager
    if getattr(manager, 'exposed_stop', None):
        manager.exposed_stop()
    loop.quit()

def handle_name_owner_changed(own, old, new):
    if own.startswith('org.bluez'):
        if new is None or len(str(new))==0:
            logger.info( "bluez has gone down, time to get out")
        else:
            logger.info( "bluez started, time to restart")
        stop()

def handle_adapter_added_or_removed(path, signal):
    logger.info("bluez.%s: %s" % (signal, path))
    stop()

def init():
    global manager, bus, loop, server
    
    logger.info("init")
    
    type__ = sys.argv[3].lower()

    a=list()
    for b in manager.manager.ListAdapters():
        obj = bus.get_object('org.bluez', b)
        adapter = dbus.Interface(obj, 'org.bluez.Adapter')
        a.append(str(adapter.GetProperties()['Address']))
    logger.info("Connected dongles: %s" % a)
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
    global server, manager, bus, loop
    
    try:
        server = rpyc.connect(server_, int(port))
    except:
        import time
        logger.info("server is not running")
        time.sleep(10)
        autoreload.RELOAD = True
        sys.exit(3)

    bus=dbus.SystemBus()
    gobject.threads_init()
    dbus.glib.init_threads()
    
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

    try:
        if type_ == 'scanner':
            from scanner import ScanManager
            logger.info("init scanner")
            manager = ScanManager(bus, rpc=server)
        elif type_ == 'uploader':
            logger.info("init uploader")
            from uploader import UploadManager
            manager = UploadManager(bus, rpc=server)
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
    loop=gobject.MainLoop()
    loop.run()

    # if we get here by any how then it's time to restart
    autoreload.RELOAD = True

if __name__ == '__main__':
    # connect to server
    if autoreload.isParent() and len(sys.argv) < 4:
        print "usage: %s server-ip port type" % sys.argv[0]
        sys.exit(0)
    valid_modes=['scanner', 'uploader']

    pluginsystem.find_plugins()
    valid_modes.extend(
        [ i.provides['serverxr_type'] 
            for i in pluginsystem.get_plugins('serverxr') ] )

    if sys.argv[3] not in valid_modes:
        print "not valid type, you can use any of", valid_modes
        sys.exit(0)

    autoreload.main(run, tuple(sys.argv[1:4]),{})

