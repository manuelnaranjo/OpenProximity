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
import dbus, dbus.glib, gobject
import os, sys
import rpyc

from rpyc import async

from net.aircable import autoreload

server = None
manager = None
bus = None
loop = None

from utils import settings, logger

def ping():
    try:
	server.ping()
	return True
    except Exception, err:
	logger.info("ping lost connection, cause: %s" % err)
	loop.quit()
	
def exposed_ping():
    return "hi"
	
def init():
    global manager, bus, loop, server
    
    logger.info("init")
    
    type = sys.argv[3].lower()

    a=list()
    for b in manager.manager.ListAdapters():
	obj = bus.get_object('org.bluez', b)
	adapter = dbus.Interface(obj, 'org.bluez.Adapter')
    	a.append(str(adapter.GetProperties()['Address']))

    if type == 'scanner':
	server.root.scanner_register(loop.quit, manager, a, exposed_ping)
	
    elif type == 'uploader':
	server.root.uploader_register(loop.quit, manager, a, exposed_ping)
    
    logger.info("exiting init")
    
    # stupid way to make rpyc do something
#    str(server.root)
	
    return False

def run(server_, port, type_):
    global server, manager, bus, loop
    
    try:
	server = rpyc.connect(server_, int(port))
    except:
#	print "connection refused, time to exit"
	autoreload.RELOAD = True
	sys.exit(3)

    bus=dbus.SystemBus()
    gobject.threads_init()
    dbus.glib.init_threads()

    if type_ == 'scanner':
        from scanner import ScanManager
	logger.info("init scanner")
	manager = ScanManager(bus)
    elif type_ == 'uploader':
        logger.info("init uploader")
        from uploader import UploadManager
        manager = UploadManager(bus, rpc=server)

    gobject.timeout_add(100, init) # delay initialization 'til loop is running
    gobject.timeout_add(1000, ping)

    loop=gobject.MainLoop()
    loop.run()

    # if we get here by any how then it's time to restart
    autoreload.RELOAD = True

if __name__ == '__main__':
    # connect to server
    if autoreload.isParent() and len(sys.argv) < 4:
        print "usage: %s server-ip port type" % sys.argv[0]
        sys.exit(0)

    if sys.argv[3] not in ['scanner', 'uploader']:
        print "not valid type use either scanner or uploader by now"
        sys.exit(0)

    autoreload.main(run, tuple(sys.argv[1:4]),{})
