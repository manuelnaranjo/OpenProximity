#    Proximity Marketing Solution: This file is in charge of uploading a 
#        certain file to a certain device using a certain bt profile.
#    Copyright (C) 2008 Manuel Naranjo <manuel@aircable.net>
#    Copyright (C) 2007 Tadas Dailyda <tadas@dailyda.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
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

import dbus
import dbus.decorators
import dbus.glib
import gobject
from os.path import basename,splitext
from signal import *
from time import ctime

DEBUG='1'

def  debug ( *text ):
    if DEBUG == None:
        return 
    print text
    

class Upload:
    total_bytes = -1
    exec_iter = 0

    #function call backs
    connected = None
    cancelled = None
    started = None
    transfer_completed = None
    error_occurred = None
    
    
    def connectBT (self, target, uuid):
        self.bt_address = target
        self.uuid = uuid
        self.session_path = self.manager.CreateBluetoothSession(
                                    self.bt_address, self.uuid)
        
        self.session_obj = self.bus.get_object('org.openobex', 
                                    self.session_path)
        
        self.session = dbus.Interface(self.session_obj, 
                                      'org.openobex.Session')

        self.session.connect_to_signal('Connected', 
                                       self.__connected_cb)
        self.session.connect_to_signal('Disconnected', 
                                       self.__disconnected_cb)
        self.session.connect_to_signal('Closed', 
                                       self.__closed_cb)
        self.session.connect_to_signal('Cancelled', 
                                       self.__cancelled_cb)
        self.session.connect_to_signal('TransferStarted', 
                                       self.__transfer_started_cb)
        self.session.connect_to_signal('TransferProgress', 
                                       self.__transfer_progress_cb)
        self.session.connect_to_signal('TransferCompleted', 
                                       self.__transfer_completed_cb)
        self.session.connect_to_signal('ErrorOccurred', 
                                       self.__error_occurred_cb)
        
    def sendFile(self, file):
       self.session.SendFile(file)
       
    def disconnectBT(self):
        self.session.Disconnect()

    def __init__(self, bus):
        self.bus = bus
        
        manager_obj = self.bus.get_object('org.openobex', '/org/openobex')
        self.manager = dbus.Interface(manager_obj, 'org.openobex.Manager')
    
    def __connected_cb(self):
        debug('Bluetooth Connected')
        if self.connected != None:
            self.connected(self)
                    
    def __disconnected_cb(self):
        debug ('Disconnected')
        self.session.Close()
        
    def __closed_cb(self):
        debug('Closed')
        if self.closed != None:
            self.closed(self)
        
    def __cancelled_cb(self):
        debug('Transfer cancelled')
        if self.cancelled != None:
            self.cancelled(self)

    def __transfer_started_cb(self, filename, local_path, total_bytes):
        debug('Transfer started (%s, %s, %d)' % (filename, local_path, total_bytes))
        self.total_bytes = total_bytes
        transfer_info = self.session.GetTransferInfo()
        debug('-- Size           = %s' % transfer_info['Size'])
        debug('-- RemoteFilename = %s' % transfer_info['RemoteFilename'])
        debug('-- LocalPath      = %s' % transfer_info['LocalPath'])
        debug('-- Time           = ', transfer_info['Time'])
        
        if self.started != None:
            self.started(self, filename)
    
    def __transfer_progress_cb(self, bytes_transferred):
        if self.total_bytes != -1:
            debug('Progress: %d %%' % int(float(bytes_transferred)/self.total_bytes*100))
        else:
            debug('Progress')
        
    def __transfer_completed_cb(self):
        debug('Transfer completed')
        if self.transfer_completed != None:
            self.transfer_completed(self)

        
    def __error_occurred_cb(self, error_name, error_message):
        debug('Error occurred: %s: %s' % (error_name, error_message))
        if self.error_occurred != None:
            self.error_ocurred(self, error_name, error_message)
        else:
            self.disconnectBT()

def connected_test(uploader):
    file_to_send = '/home/manuel/sodastero.gif'
    uploader.sendFile(file_to_send)

def transfer_completed_test(uploader):
    uploader.disconnectBT()
    
def closed_test(uploader):
    print 'All Done'
    exit(0)
    
def cancelled(uploader):
    print 'Someone Cancelled the Upload'
    uploader.disconnectBT()


if __name__ == '__main__':
    #DEFINE THIS FIELDS FOR TESTING!!!!
    bt_address = ''
    file_to_send = ''
    target_folder = ''

    gobject.threads_init()
    dbus.glib.init_threads()

    tester = Upload(dbus.SystemBus())
    tester.connectBT(bt_address, 'opp')
    tester.connected = connected_test
    tester.closed = closed_test
    tester.cancelled = cancelled
    

    main_loop = gobject.MainLoop()
    main_loop.run()

