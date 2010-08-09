# -*- coding: utf-8 -*-
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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
import dbus, dbus.service, time, os, rpyc
import net.aircable.const as const
import net.aircable.utils as utils
import net.aircable.openproximity.signals as signals
import net.aircable.sdp as sdp
from net.aircable.openproximity.signals.uploader import *
from net.aircable.utils import *
from net.aircable.wrappers import Adapter
from rpyc.utils.lib import ByValWrapper
import async

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/tmp/aircable/media')
TIMEOUT = os.environ.get('TIMEOUT', '20')
     
class UploadAdapter(Adapter):
    '''
    Class to wrap an uploader. All the process is done async, this means we
    tell the upload process to start and then wait (active) until it gives us
    back some callbacks.
    '''
    
    queue = None
    # not used ?
    
    max_uploads = None
    # max aumount of simultaneous uploads
    
    slots = None
    # upload slots
    
    manager = None
    # instance of our Uploader Manager

    def __init__(self,
                    manager, 
                    max_uploads = 7, 
                    *args, 
                    **kwargs):
        Adapter.__init__(self, *args, **kwargs)

        if not self.is_aircable:
            # Ok you got me, this is the second piece you need to remove
            # MN but don't tell anyone.
                raise Exception("Can't use non AIRcable dongle as uploaders")

        self.max_uploads = max_uploads
        self.slots = dict( [ (i, None) for i in range(max_uploads) ] )
        self.manager = manager
        logger.debug("Initializated UploaderDongle")

    def completed(self, target):
	''' 
	free up our uploading slot
	'''
	#target.cleanup()
        self.slots[target.slot] = None
        logger.info("slot %s is now free" % target.slot)

    def FileUploaded(self, target, *args, **kwargs):
	'''
	Callback that lets us know when an upload process completed succesfully.
	'''
        logger.info("File uploaded %s" % target.target)
        
        self.manager.tellListeners(
            signal = FILE_UPLOADED,
            dongle = self.bt_address,
            address = str(target.target),
            port = target.channel,
            files = ByValWrapper(target.files)
        )
        self.completed(target)

    def FileFailed(self, target, retcode, stdout, stderr, *args, **kwargs):
	'''
	Callback that lets us know when an upload process completed with a failure.
	'''
        logger.info("File Failed %s" % target.target)
        self.manager.tellListeners(
            signal=FILE_FAILED,
            address=str(target.target),
            dongle=self.bt_address,
            port=target.channel,
            ret = retcode,
            files = ByValWrapper(target.files), 
            stdout = stdout, 
            stderr = stderr,
            timeout = TIMEOUT
        )
        self.completed(target)

    def ChannelResolved(self, target, channel):
	'''
	Callback that let us know when the channel for the remote deivce has 
	been resolved correctly.
	'''
        logger.info("ChannelResolved %s -> %s" % ( target.target, channel ))
        self.manager.tellListeners(
            signal = SDP_RESOLVED,
            dongle = self.bt_address,
            address = str(target.target),
            port = channel
        )
        target.channel = channel
	self.do_upload(target)

    def do_upload(self, target):
	'''
	This function is called once we have resolved the channel.
	Is public available so we can force upload to a certain channel.
	'''
        target.SendFiles(
            channel=target.channel, 
            files=[ os.path.join(MEDIA_ROOT, f[0]) for f in target.files ],
            service = target.service,
            reply_callback=self.FileUploaded,
            error_callback=self.FileFailed
        )
    
    def ServiceNotProvided(self, target, error, state, connected):
	'''
	Callback that will get call when channel resolving failed.
	'''
        logger.info("ServiceNotProvided %s %s %s" % (target.target, error, connected))
        signal = SDP_NORECORD if connected else SDP_TIMEOUT 
        
        self.manager.tellListeners(
            signal = signal,
            dongle = self.bt_address,
            address = str(target.target)
        )
        
        self.completed(target)

    def getSlot(self):
	'''
	Function that will get called when a new upload needs an upload slot.
	If none is available we raise an Exception.
	'''
        for slot in self.slots:
            if not self.slots[slot]:
                logger.debug("found slot %s" % slot)
                return slot
        raise Exception("No slot available")


    def upload(self, files, target, uuid, service, channel=None):
	'''
	Function that gets called by the manager when it wants to do an upload.
	If no channel is provided then it will start an sdp resolving for the 
	service uuid.
	'''
        logger.debug("got an upload request %s" % target)
        sl = self.getSlot()
    
        target = async.UploadTarget(self.dbus_interface, target, self.bus)
        self.slots[sl]
    
        target.files = files
        target.slot = sl
        target.service = service
        target.uuid = uuid
    
	if not channel:
	  target.ResolveChannel(
            uuid, 
            self.ChannelResolved,
            self.ServiceNotProvided)
	else:
	  target.channel=int(channel)
	  logger.debug("Using fixed channel %s" % channel)
	  self.do_upload(target)
  
class UploadManager:
    '''
    A manager that will handle the work for the different dongles we have 
    connected.
    '''

    __dongles = dict()
    # dongles we're working with (UploadAdapter instances)

    bus = None
    # a connection to dbus

    manager = None
    # an instance of the BlueZ manager

    __sequence = list()
    # when multiple dongles are available then we try to do balance loading
    # by sending requests to each the dongles one at the time.

    __index = None
    # an index to know which dongle we used last.

    uploaders = dict()
    # dongles the server told us to use, this dict has address and priority

    def __init__(self, bus, rpc=None):
        logger.debug("UploadManager created")
        self.bus = bus
        self.manager = dbus.Interface(bus.get_object(const.BLUEZ, const.BLUEZ_PATH), const.BLUEZ_MANAGER)
        self.rpc = rpc
        if self.rpc:
            self.remote_listener=rpyc.async(self.rpc.root.listener)

    def exposed_refreshUploaders(self):
	'''
	Exposed method that lets the server tell us when it sent us all the 
	dongles so we can create a sequence of them.
	'''
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
                path=self.manager.FindAdapter(i)
            )
            self.__dongles[i] = adapter
        
        self.tellListeners(DONGLES_ADDED)
        self.__generateSequence()
        return True
    
    def __generateSequence(self):
	'''
	Internal method to generate a sequence of dongles.
	'''
        logger.debug('uploaders generating sequence')
        priority=dict()
        slots = 0
        __sequence=list()
        for dongle in self.__dongles.itervalues():
            __sequence.append(dongle)
                
        self.__sequence=__sequence
        self.__index = 0

    def exposed_getDongles(self):
	'''
	Exposed method that lets the server know which dongles we handle.
	(not used)
	'''
        def internal_getDongles(self):
            for d in self.manager.ListAdapters():
                yield str(d.GetProperties()['Address'])    
        return list(internal_getDongles(self))

    def tellListeners(self, *args, **kwargs):
	'''
	Tell our listener we have a signal with some arguments
	'''
        logger.debug(
            "UploadManager telling listener: %s, %s" %  (
                                                            str(args), 
                                                            str(kwargs)
                                                        )
            )
        self.remote_listener(*args, **kwargs)
        logger.debug("UploadManager signal dispatched")

    def __rotate_dongle(self):
	'''
	Once each upload request gets into our queue we have to go to the next 
	dongle in the sequence.
	'''
        if len(self.__sequence) == 1:
            return
            
        self.__index += 1
        if self.__index >= len(self.__sequence):
            self.__index = 0
        self.tellListeners(
                CYCLE_UPLOAD_DONGLE, 
                address=str(self.__sequence[self.__index].bt_address)
        )
        logger.debug(
            'UploadManager dongle rotated, dongle: %s' % 
                    self.__sequence[self.__index]
        )

    def exposed_upload(self, files, target, service='opp', dongle_name=None, 
	    channel=None, uploader=None):
	'''
	Exposed method that lets the server tell us it has an upload request for 
	us.
	'''
        try:
    	    dongle = None
    	    if uploader:
    		for d in self.__sequence:
    		    if d.address.bt_address.lower() == uploader.lower():
    			dongle = d
    			break

    	    if not dongle:
        	dongle=self.__sequence[self.__index]
            uuid = const.UUID[service]

            logger.debug("about to set dongle name to %s" % dongle_name)
            if dongle_name:
                dongle.dbus_interface.SetProperty('Name', dongle_name)

            logger.debug("uploading %s %s %s %s" % ( files, target, uuid, channel ) )

            for file_, fk in files:
                f = os.path.join(MEDIA_ROOT, file_)
                d = os.path.dirname(f)
                if not os.path.isdir(d) or os.path.basename(f) not in os.listdir( d ):
                    logger.debug("grabbing file %s" % d)
                    os.system('mkdir -p %s' % d )
                    A=file(f, 'w')
                    A.write(self.rpc.root.getFile(file_))
                    A.close()

            logger.debug('adding to queue')
            dongle.upload( files, target, uuid, service, channel )
            self.__rotate_dongle()
            logger.debug("upload in queue")
        except Exception, err:
            logger.error("Failed on upload")
            logger.exception(err)
            raise err

    def exposed_add_dongle(self, address, conns, name):
	'''
	This method gets called by the server during
	'''
        self.uploaders[address]=(conns, name)
        
    def exposed_stop(self):
	'''
	Exposed method to force upload stopping.
	(not used or valid at all!)
	'''
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

