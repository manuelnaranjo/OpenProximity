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

import const, dbus, dbus.service, rpyc, time, gobject, os
import signals
import protocol
from asyncsocket import BluetoothAsyncSocket
from socket import error as SocketError
from net.aircable.utils import *
from net.aircable.wrappers import Adapter
from threading import Thread, activeCount
from rpyc.utils.lib import ByValWrapper
from functools import partial
import asyncpipe

from streamserver import StreamServer

from re import compile

CAPTURE_SIZE=compile(".*\$SZE\s*(?P<size>\d+).*")

class FSM():
    CONNECTING, \
	WELCOME, \
	SETUP, \
	IDLE, \
	ASK_SIZE, \
	GET_SIZE, \
	STREAM = range(7)

class CameraConnection():
    port = 10000 # class variable

    client = None # instance variables
    target = None
    adapter = None
    state = None
    index = 0
    waiting_for_stop = False
    server_socket = None
    size = None

    def __init__(self, target, adapter, size=None):
    	self.client = BluetoothAsyncSocket()
    	self.adapter = adapter
	self.client.bind( (self.adapter.bt_address, 0) )
	self.target = target
	self.target_t = (target, 1)
	self.size = size if size else 'QQVGA'
	self.streamserver = StreamServer('0.0.0.0', CameraConnection.port)
	self.streamserver.create_server_socket()
	CameraConnection.port+=1

    def connected(self):
	logger.info("got connected")
	self.state = FSM.WELCOME
	self.client.setReadReady(self.data_available)
	if len(self.client.read_buffer) > 0:
	    self.do_welcome()

    def connection_failed(self, condition):
    	self.client.setCallback(None)
	self.client.setErrCallback(None)
	self.client.setReadReady(None)
	self.adapter.disconnected(self.target)

    def disconnect(self):
	self.client.setCallback(None)
	self.client.setErrCallback(None)
	self.client.setReadReady(None)
	self.adapter.disconnected(self.target)
	self.client.close()

    def connect(self):
	self.state  = FSM.CONNECTING
	logger.info("connecting to %s from %s" % (self.target_t, 
					self.adapter.bt_address))

	if self.adapter.manager.zm_backend:
	    self.pipe = '/tmp/camera_%s.pipe' % (self.target)

	    if not os.path.exists(self.pipe):
		os.mkfifo(self.pipe)

	return self.client.connect_ex( 
		self.target_t, 
		self.connected,  
		self.connection_failed)

    def do_welcome(self):
	if 'ACK0000' not in self.client.read_buffer:
	    return

	logger.info("got welcome")
	self.client.read_buffer = ""

	self.state = FSM.SETUP
	protocol.set_command_mode(self.client)
	protocol.set_capture_mode(self.client, size=self.size)
	self.state = FSM.IDLE
	gobject.timeout_add(200,self.take_picture)

    def take_picture(self):
	logger.info("taking picture")
	self.state = FSM.STREAM
	protocol.send_command(self.client, "SET_PREVIEW_MODE")
	#gobject.timeout_add(300,self.ask_size)
	return False

    def ask_size(self):
	if self.state != FSM.ASK_SIZE:
	    return
	logger.info("asking size")
	self.state = FSM.GET_SIZE
	protocol.send_command(self.client, 'GET_CAPTURE_SIZE')

    def get_size(self):
	if not CAPTURE_SIZE.match(self.client.read_buffer):
	    return

	size = CAPTURE_SIZE.match(self.client.read_buffer).groupdict()['size']
	self.size = size
	logger.info("got size %s" % size)
	self.state = FSM.STREAM
	protocol.send_command(self.client, 'START_CAPTURE_SEND')

    def extract_picture(self, start, end):
	logger.info("got picture")

	self.streamserver.send_to_all(
	    self.client.read_buffer[start:end+2],
	    mimetype='image/jpeg'
	)

	if self.adapter.manager.zm_backend:
	    logger.info("writing %i bytes" % (end-start))
	    asyncpipe.write(self.pipe, self.client.read_buffer[start:end+2])

	if self.adapter.manager.op_backend:
	    self.adapter.manager.tellListener(
		signals.HANDLE_PICTURE,
		dongle = self.adapter.bt_address,
	        target = self.target,
		picture = self.client.read_buffer[start:end+2]
	    )
	self.index+=1
        self.client.read_buffer = self.client.read_buffer[end+2:]

    def wait_for_prompt(self):
	logger.info("wait for prompt")
	if time.time() - self.last > 2:
	    logger.info("2 seconds without data, disconnect")
	    self.disconnect()
	    return False
	return True

    def do_stream(self):
	start, end = protocol.find_jpeg(self.client.read_buffer)

	if start > -1 and end > -1:
	    self.extract_picture(start, end)
	    if self.index == -100:
		protocol.send_command(self.client, 'SET_COMMAND_MODE')
		self.state = FSM.IDLE
		self.last = time.time()
		gobject.timeout_add(100, self.wait_for_prompt)

    def data_available(self, amount):
	if self.state == FSM.WELCOME:
	    self.do_welcome()
	elif self.state == FSM.SETUP:
	    self.do_setup()
	elif self.state == FSM.IDLE:
	    logger.info("ignoring I'm in idle")
	    self.last = time.time()
	    self.client.read_buffer = ""
	elif self.state == FSM.ASK_SIZE:
	    self.ask_size()
	elif self.state == FSM.GET_SIZE:
	    self.get_size()
	elif self.state == FSM.STREAM:
	    self.do_stream()
	else:
	    logger.debug("not valid state %s" % self.state)

class CameraAdapter(Adapter):
    def __init__(self, manager, max_conn = 7, *args, **kwargs):
        Adapter.__init__(self, *args, **kwargs)

	self.max_conn = max_conn
	self.current_connections = 0

	self.manager = manager
	self.connections = dict()
	logger.debug("Initializated CameraAdapter")

    def disconnected(self, target):
	self.connections.pop(target)
	self.manager.disconnected(target)

    def disconnect(self, target, signal):
	self.connections[target].disconnect()

    def connect(self, target, service="spp", channel=-1, size=None):
	if len(self.connections) >= self.max_conn:
	    self.manager.tellListener(signals.TOO_BUSY, 
				    dongle=self.bt_address, target=target)
	    return False

	client = CameraConnection(target, self, size)
	if not client.connect():
	    self.manager.tellListener(signals.TOO_BUSY, 
				    dongle=self.bt_address, target=target)
	    return False

	self.connections[target] = client
	logger.debug("appended to list of connections")

	return True

class CameraManager:
	__dongles = dict()
	bus = None
	manager = None
	__sequence = list()
	__index = 0
	dongles=dict()
	connections=dict()
	op_backend = False
	zm_backend = False

	def __init__(self, bus, rpc=None):
	    logger.info("CameraManager created")
	    self.bus = bus
	    self.manager = dbus.Interface(bus.get_object(const.BLUEZ, const.BLUEZ_PATH), const.BLUEZ_MANAGER)
	    self.rpc = rpc
	    if self.rpc:
	        self.remote_listener=rpyc.async(self.rpc.root.listener)

	def exposed_add_dongle(self, dongle, max_conn):
	    logger.info("add_dongle %s, %s" % (dongle, max_conn))
	    self.dongles[dongle]=max_conn

	def exposed_refreshDongles(self):
	    logger.debug("refreshDongles")
	    if self.dongles is None or len(self.dongles)==0:
		self.__dongles=dict()
		self.tellListener(signals.NO_DONGLES)
		return False

	    for i in self.dongles:
		adapter = CameraAdapter(self,
		    max_conn=self.dongles[i],
		    bus=self.bus,
		    path=self.manager.FindAdapter(i))
		self.__dongles[i]=adapter
	    self.tellListener(signals.DONGLES_ADDED)
	    self.__generateSequence()
	    return True

	def __generateSequence(self):
    	    logger.debug('camera generating sequence')
    	    priority=dict()
	    slots = 0
	    __sequence=list()
	    for dongle in self.__dongles.itervalues():
		__sequence.append(dongle)
	    self.__sequence=__sequence
	    self.__index = 0

	def __rotate_dongle(self):
	    if len(self.__sequence)==1: return

	    self.__index+=1
	    if self.__index>=len(self.__sequence): self.__index=0
	    self.tellListener(
		signals.CYCLE_CAMERA_DONGLE, 
		address=str(self.__sequence[self.__index].bt_address))
	    logger.debug('camera dongle rotated')

	def tellListener(self, *args,**kwargs):
	    try:
		logger.info("telling listener, %s, %s" % (args, kwargs))
		self.remote_listener(*args,**kwargs)
	    except Exception, err:
		logger.exception(err)

	def disconnected(self, target):
	    client = self.connections[target]
	    self.connections.pop(target)
	    self.tellListener(signals.DISCONNECTED, 
		    dongle = str(client.bt_address),
		    target= str(target))

	def exposed_disconnect(self, target):
	    client = self.connections[target]
	    self.disconnected(target)
	    client.disconnect()

	def exposed_connect(self, target, service="spp", channel=-1, size=None):
	    if target in self.connections:
		raise Exception("All ready connected to %s" % target)
	    self.connections[target]=None
	    logger.info("connect to %s" % target)
	    dongle=self.__sequence[self.__index]
	    if dongle.connect(target=target, 
				service=service, 
				channel=channel, 
				size=size):
		self.connections[target]=dongle

	def exposed_setZoneMinderBackend(self, value):
	    self.zm_backend = value

	def exposed_setOpenProximityBackend(self, value):
	    self.op_backend = value
