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
import const, dbus, dbus.service
import utils
#from database import manager
import net.aircable.openproximity.signals as signals
import sdp, subprocess, procworker, time, os, rpyc
from net.aircable.openproximity.signals.uploader import *
from utils import *
from threading import Thread
from rpyc.utils.lib import ByValWrapper
from wrappers import Adapter


# TODO add hci connection handling for detecting real timeout or out of range
def doWork(dongle_path, bt_address, files, target, service, uuid, out, semaphore): #, manager):
    logger.debug('UploaderAdapter doWork')
    bus = dbus.SystemBus(private=True)
    adapter = dbus.Interface( bus.get_object(const.BLUEZ, dongle_path), const.BLUEZ_ADAPTER )

    semaphore.acquire()
    logger.debug("Uploader resolving channel for %s, %s" % (target, service))
    try:
	port=sdp.resolve(target, uuid, adapter, bus)
    except Exception, err:
	print err
	semaphore.release()
	logger.debug("Uploader failed to resolve service %s" % (target))
	out.put({
	    'signal':SDP_NORECORD,
	    'dongle':bt_address, 
	    'address':str(target)
	    })
	return
    semaphore.release()
    logger.debug("Uploader resolved service %s, %s" % (target, port))
    out.put(
	{
	 'signal':SDP_RESOLVED, 
	 'dongle':bt_address,
	 'address':str(target),
	 'port':port
	}
    )

    arguments = list()
    arguments += ('/usr/bin/obexftp', '-d', bt_address )
    arguments += ('-r', '1' )
    if service == 'opp':
	arguments += ('-U', 'none', '-H', '-S' )
    arguments += ('-T', str(settings.TIMEOUT) )
    arguments += ('-b', target )
    arguments += ('-B', str(port) )
    for f, fk in files:
	arguments += ('-p', os.path.join(settings.MEDIA_ROOT, f) )
    proc = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    logger.debug("Uploader calling obexftp for %s on channel %s" % (target, port))
    (stdout, stderr) = proc.communicate()
    print stdout
    print stderr
    retcode = proc.returncode
    logger.debug("Uploader obexftp completed for %s, result %s" % (target, retcode))

    if retcode==0 or retcode==255: # bug in my patch, it gives negative ret code
	out.put({
	    'signal': FILE_UPLOADED, 
	    'dongle': bt_address,
	    'address': str(target), 
	    'port': port,
	    'files': ByValWrapper(files)
	    })
    else:
	out.put({
	    'signal': FILE_FAILED,
	    'address': str(target),
	    'dongle': bt_address,
	    'port': port,
	    'ret': retcode,
	    'files': ByValWrapper(files), 
	    'stdout': stdout, 
	    'stderr': stderr
	})
    logger.debug("Uploader dowork finished")

def proxy_messages(manager, queue):
    logger.debug("message proxy started")
    while [ 1 ]:
	kwargs = queue.get(True)
	logger.debug('got a message from queue, sending over rpyc')
	manager.tellListeners(**kwargs)

class UploadAdapter(Adapter):
	queue = None

	def __init__(self, manager, max_uploads = 7, *args, **kwargs):
    	    Adapter.__init__(self, *args, **kwargs)

	    if not self.is_aircable:
		# Ok you got me, this is the second piece you need to remove
		# MN but don't tell anyone.
	        raise Exception("Can't use non AIRcable dongle as uploaders")

	    self.max_uploads = max_uploads
	    self.current_connections = 0

	    self.worker = procworker.Manager(max_uploads)
	    self.worker.start()
#	    self.semaphore = procworker.Lock()
	    self.manager = manager
	    self.proxy=Thread(target=proxy_messages, 
		kwargs={
		    'manager': manager, 
		    'queue': self.worker.out})
	    self.proxy.daemon=True
	    self.proxy.start()

	    logger.debug("Initializated UploaderDongle")
	    
	def upload(self, files, target, uuid, service):
	    logger.debug("Adding to upload queue %s" % target)

	    self.worker.put ( doWork,
		dongle_path=self.dbus_path,
		bt_address=self.bt_address,
		files=files,
		target=target,
		uuid=uuid,
#		port=port,
		service=service,
#		manager=self.manager
#		semaphore=self.semaphore
	    )

class UploadManager:
	__dongles = dict()
	bus = None
	manager = None
	__listener_sync = list()
	__listener_async = list()
	__sequence = list()
	__index = None
	uploaders = dict()

	def __init__(self, bus, rpc=None):
		logger.debug("UploadManager created")
		self.bus = bus
		self.manager = dbus.Interface(bus.get_object(const.BLUEZ, const.BLUEZ_PATH), const.BLUEZ_MANAGER)
		self.rpc = rpc
		if self.rpc:
		    self.remote_listener=rpyc.async(self.rpc.root.listener)

	def exposed_refreshUploaders(self):
		logger.debug("UploadManager refresh uploaders %s" % self.uploaders)
		if self.uploaders is None or len(self.uploaders) == 0:
			self.__dongles = dict()
			self.tellListeners(NO_DONGLES)
			return False

		for i in self.uploaders.keys():
			adapter = UploadAdapter(
				self,
				self.uploaders[i][0],
				name=self.uploaders[i][1],
				bus=self.bus, 
				path=self.manager.FindAdapter(i))
			self.__dongles[i] = adapter
		
		self.tellListeners(DONGLES_ADDED)
		self.__generateSequence()
		return True
	
	def __generateSequence(self):
		logger.debug('uploaders generating sequence')
		priority=dict()
		slots = 0
		__sequence=list()
		for dongle in self.__dongles.itervalues():
		    __sequence.append(dongle)
			    
		self.__sequence=__sequence
		self.__index = 0

        def exposed_getDongles(self):
            out = set()
            for d in self.manager.ListAdapters():
                out.append(str(d.GetProperties()['Address']))
	    return out
		
	def tellListeners(self, *args, **kwargs):
		logger.debug("UploadManager telling listener: %s, %s" % (str(args), str(kwargs)))
		self.remote_listener(*args, **kwargs)
		logger.debug("UploadManager signal dispatched")

	def __rotate_dongle(self):
		if len(self.__sequence) == 1:
		    return
		    
		self.__index += 1
		if self.__index >= len(self.__sequence):
			self.__index = 0
		self.tellListeners(CYCLE_UPLOAD_DONGLE, address=str(self.__sequence[self.__index].bt_address))
		logger.debug('UploadManager dongle rotated, dongle: %s' % self.__sequence[self.__index])

	def exposed_upload(self, files, target, service='opp', dongle_name=None):
	    try:
		dongle=self.__sequence[self.__index]
		uuid = const.UUID[service]
		
		print files
		print "about to set name"
		if dongle_name:
		    dongle.dbus_interface.SetProperty('Name', dongle_name)
		
		logger.debug("uploading %s %s %s" % ( files, target, uuid ) )
		
		for file_, fk in files:
		    f = os.path.join(settings.MEDIA_ROOT, file_)
		    d = os.path.dirname(f)
		    print f, d
		    if not os.path.isdir(d) or os.path.basename(f) not in os.listdir( d ):
			print "grabing file"
			os.system('mkdir -p %s' % d )
			A=file(f, 'w')
			A.write(self.rpc.root.getFile(file_))
			A.close()
		
		logger.debug('adding to queue')
		dongle.upload( files, target, uuid, service )
		self.__rotate_dongle()
		logger.debug("upload in queue")
	    except Exception, err:
		print err
		raise err
		
	def exposed_add_dongle(self, address, conns, name):
	    self.uploaders[address]=(conns, name)
	    
	def exposed_stop(self):
	    logger.info("stop called")
	    for k in self.__sequence:
		try:
		    k.worker.stop()
		    k.proxy.stop()
		except:
		    pass

	# signal callback

if __name__=='__main__':
	def listen(signal, **kwargs):
		print signal, kwargs

	import dbus
	import gobject
	import dbus.glib
	import dbus.mainloop.glib
	import threading
	import sys
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	
	manager=UploadManager(dbus.SystemBus())
	manager.remote_listener=listen
	manager.exposed_add_dongle('00:25:BF:01:00:9E',7, 'test')
	manager.exposed_refreshUploaders()
	
	gobject.threads_init()
	dbus.glib.init_threads()
	loop=gobject.MainLoop()
	manager.exposed_upload(((sys.argv[2], 1),), sys.argv[1], dongle_name='AIRcable')
	loop.run()
