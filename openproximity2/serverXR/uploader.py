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
import subprocess
import net.aircable.procworker as procworker
from net.aircable.openproximity.signals.uploader import *
from net.aircable.utils import *
from net.aircable.wrappers import Adapter
from threading import Thread
from rpyc.utils.lib import ByValWrapper
import async

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/tmp/aircable/media')
TIMEOUT = os.environ.get('TIMEOUT', '20')

class UploadAdapter(Adapter):
    queue = None

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
        self.current_connections = 0
        self.slots = dict( [ (i, None) for i in range(max_uploads) ] )
        self.manager = manager
        logger.debug("Initializated UploaderDongle")

    def completed(self, target):
	#target.cleanup()
        self.slots[target.slot] = None
        logger.info("slot %s is now free" % target.slot)

    def FileUploaded(self, target, *args, **kwargs):
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
        logger.info("ChannelResolved %s -> %s" % ( target.target, channel ))
        self.manager.tellListeners(
            signal = SDP_RESOLVED,
            dongle = self.bt_address,
            address = str(target.target),
            port = channel
        )
        target.channel = channel
        
        target.SendFiles(
            channel=channel, 
            files=[ os.path.join(MEDIA_ROOT, f[0]) for f in target.files ],
            service = target.service,
            reply_callback=self.FileUploaded,
            error_callback=self.FileFailed
        )
    
    def ServiceNotProvided(self, target, error, state, connected):
        logger.info("ServiceNotProvided %s %s %s" % (target.target, error, connected))
        signal = SDP_NORECORD if connected else SDP_TIMEOUT 
        
        self.manager.tellListeners(
            signal = signal,
            dongle = self.bt_address,
            address = str(target.target)
        )
        
        self.completed(target)

    def getSlot(self):
        for slot in self.slots:
            if not self.slots[slot]:
                logger.debug("found slot %s" % slot)
                return slot
        raise Exception("No slot available")


    def upload(self, files, target, uuid, service):
        logger.debug("got an upload request %s" % target)
        sl = self.getSlot()
    
        target = async.UploadTarget(self.dbus_interface, target, self.bus)
        self.slots[sl]
    
        target.files = files
        target.slot = sl
        target.service = service
        target.uuid = uuid
    
        target.ResolveChannel(
            uuid, 
            self.ChannelResolved,
            self.ServiceNotProvided)
  
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
                path=self.manager.FindAdapter(i)
            )
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
            def internal_getDongles(self):
                for d in self.manager.ListAdapters():
                    yield str(d.GetProperties()['Address'])    
            return list(internal_getDongles(self))

    def tellListeners(self, *args, **kwargs):
        logger.debug(
            "UploadManager telling listener: %s, %s" %  (
                                                            str(args), 
                                                            str(kwargs)
                                                        )
            )
        self.remote_listener(*args, **kwargs)
        logger.debug("UploadManager signal dispatched")

    def __rotate_dongle(self):
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

    def exposed_upload(self, files, target, service='opp', dongle_name=None):
        try:
            dongle=self.__sequence[self.__index]
            uuid = const.UUID[service]
            
            logger.debug("about to set dongle name to %s" % dongle_name)
            if dongle_name:
                dongle.dbus_interface.SetProperty('Name', dongle_name)
            
            logger.debug("uploading %s %s %s" % ( files, target, uuid ) )
            
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
            dongle.upload( files, target, uuid, service )
            self.__rotate_dongle()
            logger.debug("upload in queue")
        except Exception, err:
            logger.error("Failed on upload")
            logger.exception(err)
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

