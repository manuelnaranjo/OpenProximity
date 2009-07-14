import const
import dbus
import utils

#from database import manager
from wrappers import Adapter
from utils import logger
from utils import settings
import net.aircable.openproximity.signals as signals
from net.aircable.openproximity.signals.scanner import *
import rpyc
import time
import traceback

remotescanner_url = "net.aircable.RemoteScanner"

class ScanAdapter(Adapter):
	priority = 0
	
	def __init__(self, priority, *args, **kwargs):
		Adapter.__init__(self, *args, **kwargs)
		
		if priority is None or priority < 0:
			priority=0
			
		self.priority=int(priority)
		logger.debug("Initializated ScannerDongle: %s" % priority)
	
	def __str__(self):
		return '%s, %s' % (Adapter.__str__(self), self.priority)
	
	def scan(self):
		#traceback.print_stack()
		self.dbus_interface.StartDiscovery()
		
	def endScan(self):
		#traceback.print_stack()
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
		logger.debug("Initializated ScannerDongle: %s" % priority)
	
	def __str__(self):
		return 'RemoteScanner %s %s %s' % (
		    self.priority, self.local, self.bt_address)
	
	def scan(self):
	    if self.sending:
		return
	    self.sending = True
	    remote_object = self.bus.get_object(remotescanner_url,
		"/RemoteScanner")
	    iface = dbus.Interface(remote_object, remotescanner_url)
	    iface.StartScan(self.local, self.bt_address)
	    print "Scan started"
			
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
	    
	def __init__(self, bus, listener=None):
		logger.debug("ScanManager created")
		self.bus = bus
		self.manager = dbus.Interface(bus.get_object(const.BLUEZ, const.BLUEZ_PATH), const.BLUEZ_MANAGER)
		if listener is not None:
		    for x in listener:
			self.expoed_addListener(x)
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
			self.tellListeners(NO_DONGLES)
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
		self.tellListeners(DONGLES_ADDED)
		return True
	
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
	    
	def exposed_addListener(self, func):
		logger.debug("ScanManager adding listener")
		self.__listener.append(rpyc.async(func))
		
	def tellListeners(self, *args, **kwargs):
		logger.debug("ScanManager telling listener: %s, %s" % (str(args), str(kwargs)))
		for func in self.__listener:
			func(*args, **kwargs)
			
	def exposed_startScanningCycle(self, repeat=False):
	    self.tellListeners(CYCLE_START)
	    self.__index = 0
	    self.__repeat = repeat
	    self.__do_scan()
	
	def exposed_getDongles(self):
	    out = set()
	    for d in self.manager.ListAdapters():
		out.append(str(d.GetProperties()['Address']))
	    return out

	def exposed_add_dongle(self, address, priority, name):
	    self.scanners[address]=(priority, name)
	    
	def __do_scan(self):
	    logger.debug('ScanManager scanning on dongle')

	    if self.__index < len(self.__sequence):
		self.__found=dict()
		self.__sequence[self.__index].scan()
	
	def __rotate_dongle(self):
		self.__index += 1
		if self.__index >= len(self.__sequence):
			self.__index = 0
		self.tellListeners(CYCLE_SCAN_DONGLE, address=str(self.__sequence[self.__index].bt_address))
		logger.debug('ScanManager dongle rotated, dongle: %s' % self.__sequence[self.__index])
			
	# signal callbacks		
	def device_found(self, address, values, path=None):
            if address not in self.__found:
                    self.__found[address] = dict()
		    self.__found[address]['rssi'] = list()
		    
	    if 'name' not in self.__found[address] and 'Name' in values:
		self.__found[address]['name']=str(values['Name'])
	    if  'devclass' not in self.__found[address] and 'Class' in values:
		self.__found[address]['devclass'] = int(values['Class'])
		
	    self.__found[address]['rssi'].append(int(values['RSSI']))
	    logger.debug('Device found: %s %s' % (address, self.__found[address]))
	    
	def property_changed(self, name, value, path=None):
	    if name=='Discovering':
		if value==0:
		    logger.debug('Discovery completed for path: %s' % path)
		    self.__sequence[self.__index].endScan()
		    self.discovery_completed()
		    return
		else:
		    logger.debug('Discovery started for path: %s' % path)
		    return
	    print name, value, path
	    
			
	def discovery_completed(self):
		founds = list()
		
		for found,data in self.__found.iteritems():
			founds.append(
			    { 
				'address': str(found), 
				'name': str(getattr(data, 'name', None)),
				'rssi': data['rssi'],
				'devclass': int(getattr(data,'devclass',-1))
			    }
			)

		if len(founds) > 0:
		    self.tellListeners(signal=FOUND_DEVICE, 
			address=str(self.__sequence[self.__index].bt_address),
			records=founds)
		
		self.__rotate_dongle()
		if self.__index > 0:
			self.__do_scan()
		elif self.__repeat:
			self.startScanningCycle(self, repeat)
		else:
			self.tellListeners(CYCLE_COMPLETE)
		
		return False

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
