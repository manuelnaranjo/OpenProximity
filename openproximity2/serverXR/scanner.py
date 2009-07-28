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
import const, dbus, utils, rpyc, time, traceback

#from database import manager
from wrappers import Adapter
from utils import logger
from utils import settings
from net.aircable.openproximity.signals.scanner import *
from pickle import dumps

import net.aircable.openproximity.signals as signals

remotescanner_url = "net.aircable.RemoteScanner"

class ScanAdapter(Adapter):
	priority = 0
	found = None
	
	def __init__(self, priority, *args, **kwargs):
		Adapter.__init__(self, *args, **kwargs)
		
		if priority is None or priority < 0:
			priority=0
			
		self.priority=int(priority)
		logger.debug("Initializated ScannerDongle: %s" % priority)
	
	def __str__(self):
		return '%s, %s' % (Adapter.__str__(self), self.priority)
	
	def scan(self):
	    self.found = dict()
	    self.dbus_interface.StartDiscovery()
		
	def endScan(self):
	    self.dbus_interface.StopDiscovery()

class RemoteScanAdapter(ScanAdapter):
	priority = 0
	sending = False
	
	def __init__(self, priority, local=None, address=None, bus=None):
		if priority is None or priority < 0:
			priority=0
			
		self.priority=int(priority)
		self.local = local
		self.bt_address = address
		self.bus = bus
		
		manager = self.bus.get_object(remotescanner_url,
		    "/net/aircable/RemoteScanner/Manager")
		self.dbus_path = manager.Connect(dbus_interface=remotescanner_url)
		
		remote_object = self.bus.get_object(remotescanner_url, self.dbus_path)
		
		self.iface = dbus.Interface(remote_object, remotescanner_url)

		logger.debug("Initializated RemoteScannerDongle: %s" % priority)
	
	def __str__(self):
		return 'RemoteScanner %s %s %s' % (
		    self.priority, self.local, self.bt_address)
	
	def scan(self):
	    if self.sending:
		return
	    
	    if not self.iface.isConnected():
		self.iface.Connect(self.local, self.bt_address)
	
	    self.sending = True
	    self.found = dict()
	    self.iface.StartScan(1)
	    logger.debug("Scan started")

	def endScan(self):
	    self.sending = False

class ScanManager:
	__dongles = dict()
	bus = None
	manager = None
	__listener = list()
	__sequence = list()
	__index = None
	__repeat = False
	scanners = dict()
	concurrent = False
	concurrent_pending = list()
	    
	def __init__(self, bus, listener=None):
		logger.debug("ScanManager created")
		self.bus = bus
		self.manager = dbus.Interface(bus.get_object(const.BLUEZ, const.BLUEZ_PATH), const.BLUEZ_MANAGER)
		if listener is not None:
		    for x in listener:
			self.exposed_addListener(x)
		self.exposed_refreshScanners()
		
		# Subscribe to signals
		self.bus.add_signal_receiver(self.device_found, # callback
			'DeviceFound', # signal name
			'org.bluez.Adapter', # interface name
			'org.bluez', # sender bus name
			path_keyword='path') #
		
		self.bus.add_signal_receiver(self.property_changed, # callback
			'PropertyChanged', # signal name
			'org.bluez.Adapter', # interface name
			'org.bluez', # sender bus name
			path_keyword='path') #
			
		# call back for remote scanner
		self.bus.add_signal_receiver(self.property_changed, # callback
			signal_name='PropertyChanged', # signal name
			dbus_interface=remotescanner_url, # interface name
			path_keyword='path'
			)

		self.bus.add_signal_receiver(self.device_found, # callback
			signal_name='DeviceFound', # signal name
			dbus_interface=remotescanner_url, # interface name
			path_keyword='path'
			)
	
	def exposed_refreshScanners(self):
		logger.debug("ScanManager refresh scanners %s" % self.scanners)
		if self.scanners is None or len(self.scanners) == 0:
			self.__dongles = dict()
			return False
			
		for i in self.scanners.keys():
			try:
			    path=self.manager.FindAdapter(i)
			    adapter = ScanAdapter(self.scanners[i][0], 
				name=self.scanners[i][1], 
				bus=self.bus, path=path)
			except:
			    adapter = RemoteScanAdapter(self.scanners[i][0], 
				local=self.scanners[i][1], address=i, 
				bus=self.bus)
			
			self.__dongles[i] = adapter
		
		self.__generateSequence()
		self.tellListenersAsync(DONGLES_ADDED)
	
	def __generateSequence(self):
		# we want a sequence were we interleave devices as
		# PRIORITY=2, PRIORITY=1, PRIORITY=2
		# so that dongles with higher priority will get more scanning slots
		logger.debug('scanner generating sequence')
		priority=dict()
		slots = 0
		
		for dongle in self.__dongles.itervalues(): # extract priority from __dongles
			if dongle.priority not in priority:
				priority[dongle.priority]=list()
			priority[dongle.priority].append(dongle)
			slots+=dongle.priority
		logger.debug('scanner sequence %s slots' % slots)
	    
		priorities=priority.keys()
		priorities.sort(reverse=True) # this gets higher to lower priority
		__sequence = list()
		
		a=0
		for p in priorities:
			# first we add the dongles with the lowest priority
			for dongle in self.__dongles.itervalues():
				if p==dongle.priority:
					logger.debug('slot[%s] = %s' % (a, dongle))
					__sequence.append(dongle)
					a+=1

		for dongle in self.__dongles.itervalues():
			if p < dongle.priority:
				logger.debug('slot[%s] = %s' % (a, dongle))
				__sequence.append(dongle)
				a+=1
	    
		self.__sequence=__sequence
		self.__index = 0
		
	def exposed_setConcurrent(self, val):
	    self.concurrent = val
	
	def exposed_getConcurrent(self):
	    return self.concurrent
	    
	def exposed_addListener(self, func):
		logger.debug("ScanManager adding listener")
		self.__listener.append(func)
		
	def tellListenersSync(self, *args, **kwargs):
	    logger.debug("ScanManager telling listener - sync: %s, %s" % (str(args), str(kwargs)))
	    for func in self.__listener:
	    	func(*args,**kwargs)
	
	def tellListenersAsync(self, *args, **kwargs):
	    logger.debug("ScanManager telling listener - async: %s, %s" % (str(args), str(kwargs)))
	    for func in self.__listener:
		rpyc.async(func)(*args, **kwargs)

	def exposed_startScanningCycle(self, repeat=False):
	    self.tellListenersSync(CYCLE_START)
	    self.__index = 0
	    self.__repeat = repeat
	    if self.concurrent:
		self.pending=list()
	
	def exposed_getDongles(self):
	    out = set()
	    for d in self.manager.ListAdapters():
		out.append(str(d.GetProperties()['Address']))
	    return out

	def exposed_add_dongle(self, address, priority, name):
	    self.scanners[address]=(priority, name)
	    
	def exposed_doScan(self):
	    logger.debug('ScanManager scanning')
	    
	    if not self.concurrent:
		self.__do_scan_no_concurrent()
	    else:
		self.__multi_scan()
	    
	def __do_scan_no_concurrent(self):
	    logger.debug("No concurrent scan")
	    logger.debug('ScanManager scanning on dongle: %s' % self.__sequence[self.__index].bt_address)
	    if self.__index < len(self.__sequence):
		try:
		    self.__sequence[self.__index].scan()
		except Exception, err:
		    logger.debug("Couldn't scan, error: %s" % err)
		    self.__sequence[self.__index].endScan()
		    addr = str(self.__sequence[self.__index].bt_address)
		    ret=self.__rotate_dongle()
		    if not ret:
			self.tellListenersSync(DONGLE_NOT_AVAILABLE, 
			    address=addr)
			    
	def __multi_scan(self):
	    logger.debug("Concurrent scan")
	    print len(self.pending)
	    if self.pending is not None and len(self.pending) > 0:
		raise Exception("Can't do multiple concurrent scans if pending")
	    self.pending = list()
	    for dongle in self.__dongles.itervalues():
		print dongle.dbus_path, "scanning"
		dongle.scan()
		self.pending.append(dongle.dbus_path)
		
	
	def __rotate_dongle(self):
		self.__index += 1
		if self.__index >= len(self.__sequence):
		    self.tellListenersSync(CYCLE_COMPLETE)
		    self.__index = 0
		    logger.debug('ScanManager dongle cycle completed')
		    return True
		logger.debug('ScanManager dongle rotated, dongle: %s' % self.__sequence[self.__index])
		return False
	
	def __getScannerForPath(self, path):
	    for dongle in self.__dongles.itervalues():
		if dongle.dbus_path == path:
		    return dongle
	    raise Exception("Path not Valid")
			
	# signal callbacks		
	def device_found(self, address, values, path=None):
	    dongle = self.__getScannerForPath(path)
	    
            if address not in dongle.found:
                    dongle.found[address] = dict()
		    dongle.found[address]['rssi'] = list()
		    dongle.found[address]['time'] = list()
		    
	    if 'name' not in dongle.found[address] and 'Name' in values:
		dongle.found[address]['name']=str(values['Name'])
	    if  'devclass' not in dongle.found[address] and 'Class' in values:
		dongle.found[address]['devclass'] = int(values['Class'])
		
	    dongle.found[address]['rssi'].append(int(values['RSSI']))
	    dongle.found[address]['time'].append(time.time())
	    logger.debug('%s device found: %s' % (path, address) )
	    
	def property_changed(self, name, value, path=None):
	    if self.__index == None:
		return
	    if name=='Discovering':
		if value==0:
		    logger.debug('Discovery completed for path: %s' % path)
		    dongle = self.__getScannerForPath(path)
		    dongle.endScan()
		    if self.concurrent:
			self.pending.remove(dongle.dbus_path)
		    self.discovery_completed(dongle)
		    return
		else:
		    logger.debug('Discovery started for path: %s' % path)
		    return
	    logger.debug("property_changed %s %s %s" % (name, value, path) )
	
	def exposed_cycleCompleted(self):
	    return self.__index == len(self.__sequence) - 1
			
	def discovery_completed(self, dongle):
		founds = list()
		
		for found,data in dongle.found.iteritems():
			founds.append(
			    { 
				'address': str(found), 
				'name': str(getattr(data, 'name', None)),
				'rssi': data['rssi'],
				'time': data['time'],
				'devclass': int(getattr(data,'devclass',-1))
			    }
			)

		addr=str(dongle.bt_address)
		
		if len(founds) > 0:
		    self.tellListenersSync(signal=FOUND_DEVICE, 
			address=str(dongle.bt_address),
			records=dumps(founds) )
		
		if not self.concurrent:
		    ret=self.__rotate_dongle()
		    if not ret:
			self.tellListenersSync(CYCLE_SCAN_DONGLE_COMPLETED,
			    address=addr)
		elif len(self.pending) == 0:
		    self.tellListenersSync(CYCLE_SCAN_DONGLE_COMPLETED,
			    address=addr)

		    

if __name__=='__main__':
	def listen(signal, **kwargs):
		print signal, TEXT[signal], kwargs, signals.isScannerSignal(signal)
		
		if signal == CYCLE_COMPLETE:
			loop.quit()

	import dbus
	import gobject
	import dbus.glib
	import dbus.mainloop.glib
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	
	manager=ScanManager(dbus.SystemBus(), [ listen, ])
	manager.scanners['00:50:C2:7F:EF:FE']=1
	
	gobject.threads_init()
	dbus.glib.init_threads()
	loop=gobject.MainLoop()
	manager.exposed_startScanningCycle()
	loop.run()
