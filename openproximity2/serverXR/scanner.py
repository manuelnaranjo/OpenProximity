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
import dbus, rpyc, time, traceback, gobject
from net.aircable.utils import logger
from net.aircable.openproximity.signals.scanner import *
from net.aircable.wrappers import Adapter
from rpyc.utils.lib import ByValWrapper
from django.utils.encoding import smart_str

import net.aircable.const as const
import net.aircable.utils as utils
import net.aircable.openproximity.signals as signals

remotescanner_url = "net.aircable.RemoteScanner"

class ScanAdapter(Adapter):
    '''
    Wrapper arround a BlueZ scanner
    '''
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
        '''
        Call this function to start a scan process on this dongle
        '''
        self.found = dict()
        self.dbus_interface.StartDiscovery()
        
    def endScan(self):
        '''
        Force ongoing inquiry to stop
        '''
        self.dbus_interface.StopDiscovery()

class RemoteScanAdapter(ScanAdapter):
    '''
    Wrapper arround a scanner to which we connect over bluetooth.
    '''
    priority = 0
    sending = False
    
    def __init__(self, 
                priority, 
                local=None, 
                address=None, 
                bus=None, 
                scanner_manager=None):
        if priority is None or priority < 0:
            priority=0
            
        self.priority=int(priority)
        self.local = local
        self.bt_address = address
        self.bus = bus
        self.scanner_manager = scanner_manager
        
        manager = self.bus.get_object(
            remotescanner_url,
            "/net/aircable/RemoteScanner/Manager"
        )
        self.dbus_path = manager.Connect(dbus_interface=remotescanner_url)
        
        remote_object = self.bus.get_object(remotescanner_url, self.dbus_path)
        
        self.iface = dbus.Interface(remote_object, remotescanner_url)
        
        self.bus.add_signal_receiver(
            self.connected, # callback
            signal_name='ScannerConnected', # signal name
            dbus_interface=remotescanner_url, # interface name
        )

        self.bus.add_signal_receiver(
            self.disconnected, # callback
            signal_name='ScannerDisconnected', # signal name
            dbus_interface=remotescanner_url, # interface name
        )

        logger.debug("Initializated RemoteScannerDongle: %s" % priority)
    
    def connected(self, local, remote):
        '''
        Callback that lets us know when we got connected to the remote scanner
        '''
        if self.bt_address.lower() == remote.lower():
            logger.info("scanner connected %s" % remote)
            self.scanner_manager.property_changed(
                'Discovering',
                0,
                self.dbus_path
            )

    def disconnected(self, local, remote):
        '''
        Callback that lets us know when we got disconnected to the remote 
        scanner
        '''
        if self.bt_address.lower() == remote.lower():
            logger.info("scanner disconnected %s" % remote)
            self.scanner_manager.property_changed(
                'Discovering',
                0,
                self.dbus_path
            )

    
    def __str__(self):
        return 'RemoteScanner %s %s %s' % (
            self.priority, self.local, self.bt_address)
    
    def scan(self):
        '''
        Start a scan in the remote scanner
        '''
        if self.sending:
            return
        
        if not self.iface.isConnected():
            self.iface.Connect(self.local, self.bt_address)
            return
    
        self.sending = True
        self.found = dict()
        self.iface.StartScan(1)
        logger.debug("Scan started")

    def endScan(self):
        '''
        Stop the pending inquiry (has no effect on the RemoteScanner).
        '''
        self.sending = False

class ScanManager:
    '''
    A scanner manager is responsible of handling all the connected scanners, 
    handling all the logic for this and communicating with the server.
    '''
    
    __dongles = dict()
    # dict that holds our in use dongles (ScanAdapter instances)
    
    bus = None
    # a connection to dbus
    
    manager = None
    # a connection to the BlueZ manager
    
    __sequence = list()
    # a holder for our scan sequence (sequence mode)
    
    __index = None
    # index in the scan sequence (sequence mode)
    
    scanners = dict()
    # dict that holds our known dongles (strings)
    
    concurrent = False
    # flag that lets us know which mode we're running
    # concurrent = False -> sequence mode (default)
    # concurrent = True  -> concurrent mode
    
    pending = None
    # list of pending scanners to complete the process for concurrent mode.
    
    def addBlueZSignalHandlers(self):
        # Subscribe to signals
        self.bus.add_signal_receiver(
            self.device_found, # callback
            'DeviceFound', # signal name
            'org.bluez.Adapter', # interface name
            'org.bluez', # sender bus name
            path_keyword='path') #
        
        self.bus.add_signal_receiver(
            self.property_changed, # callback
            'PropertyChanged', # signal name
            'org.bluez.Adapter', # interface name
            'org.bluez', # sender bus name
            path_keyword='path') #

    def addRemoteScannerSignalHandlers(self):
        # call back for remote scanner
        self.bus.add_signal_receiver(
            self.property_changed, # callback
            signal_name='PropertyChanged', # signal name
            dbus_interface=remotescanner_url, # interface name
            path_keyword='path'
            )

        self.bus.add_signal_receiver(
            self.device_found, # callback
            signal_name='DeviceFound', # signal name
            dbus_interface=remotescanner_url, # interface name
            path_keyword='path'
            )


    def __init__(self, bus, listener=None, rpc=None):
        logger.debug("ScanManager created")
        self.bus = bus
        self.manager = dbus.Interface(
                                bus.get_object(const.BLUEZ, const.BLUEZ_PATH), 
                                const.BLUEZ_MANAGER
        )
        if listener is not None:
            for x in listener:
                self.exposed_addListener(x)
        self.exposed_refreshScanners()
        
        self.addBlueZSignalHandlers() # if this fails we're dead
        
        try:
            self.addRemoteScannerSignalHandlers() 
            # this may fail and we don't care
        except:
            pass
        
        self.rpc = rpc
        if self.rpc:
            self.remote_listener=rpyc.async(self.rpc.root.listener)
    
    def exposed_refreshScanners(self):
        '''
        When called by the server this method will create ScanAdapter or 
        RemoteScanAdapter for each one of our scanner dongles and then will
        create the can sequence. Letting the server know when we are ready
        to start scanning by triggering DONGLES_ADDED
        '''
        logger.debug("ScanManager refresh scanners %s" % self.scanners)
        if self.scanners is None or len(self.scanners) == 0:
            self.__dongles = dict()
            return False
        try:
            for i in self.scanners.keys():
                try:
                    path=self.manager.FindAdapter(i)
                    adapter = ScanAdapter(self.scanners[i][0], 
                    name=self.scanners[i][1], 
                    bus=self.bus, path=path)
                except Exception, err:
                    print err
                    print "trying with a remote scanner"
                    try:
                        adapter = RemoteScanAdapter(self.scanners[i][0], 
                            local=self.scanners[i][1], address=i, 
                            bus=self.bus, scanner_manager=self)
                    except Exception, err2:
                        logger.error(err2)
                        continue
                
                self.__dongles[i] = adapter
        
            self.__generateSequence()
            self.tellListenersAsync(DONGLES_ADDED)
        except Exception, err:
            print err
            raise err
    
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
        '''
        Exposed method that lets the server tell us if we should do concurrent 
        scanning (all the scanners work at the same time), or sequence scanning.
        '''
        self.concurrent = val
        logger.info("setConcurrent %s" % val)
    
    def exposed_getConcurrent(self):
        '''
        Exposed method that lets the server know if we are in concurrent or
        sequence mode (default)
        '''
        return self.concurrent

    def tellListenersAsync(self, *args, **kwargs):
        '''
        Dispatch the given signal with the given arguments to our listener.
        '''
        logger.debug("ScanManager telling listener - async: %s" % POST[args[0]])
        self.remote_listener(*args, **kwargs)
        logger.debug("ScanManager message dispatched")

    def exposed_startScanningCycle(self):
        '''
        Exposed method that lets the server decide when we start a new scan 
        cycle this means we restart our index for sequence mode, and we drop
        out our pending scans for concurrent mode
        NOTE: this isn't very reliable, we shouldn't relay this to the server
        '''
        self.tellListenersAsync(CYCLE_START)
        self.__index = 0
        if self.concurrent:
            self.pending=list()
    
    def exposed_noCampaigns(self):
        '''
            this method gets called when there was no matching campaigns on the
            server, so we tell the server until it's ready
        '''
        def request_server(self):
            self.tellListenersAsync(CYCLE_COMPLETE)
            return False
        logger.info("no campaigns, scheduling request")
        gobject.timeout_add(60*1000, request_server, self)

    def exposed_getDongles(self):
        '''
        Exposed method that lets the server know which dongles we are handling.
        '''
        out = set()
        for d in self.manager.ListAdapters():
            out.append(str(d.GetProperties()['Address']))
        return out

    def exposed_add_dongle(self, address, priority, name):
        '''
        Exposed method that lets the server tell us which dongle use with which
        settings (name and priority)
        '''
        self.scanners[address]=(priority, name)
        
    def exposed_doScan(self):
        '''
        Exposed method that tells us to start scanning.
        '''
        logger.debug('ScanManager scanning')
        
        if not self.concurrent:
            self.__do_scan_no_concurrent()
        else:
            self.__multi_scan()
        
    def __do_scan_no_concurrent(self):
        '''
        internal method that starts a sequence scan
        '''
        logger.debug("No concurrent scan")
        if self.__index < len(self.__sequence):
            try:
                logger.debug('ScanManager scanning on dongle: %s' % self.__sequence[self.__index].bt_address)
                self.__sequence[self.__index].scan()
            except Exception, err:
                logger.debug("Couldn't scan, error: %s" % err)
                self.__sequence[self.__index].endScan()
                addr = str(self.__sequence[self.__index].bt_address)
                ret=self.__rotate_dongle()
                if not ret:
                    self.tellListenersAsync(DONGLE_NOT_AVAILABLE, address=addr)

    def __multi_scan(self):
        '''
        internal method that starts a concurrent scan
        '''
        logger.debug("Concurrent scan")
        if self.pending is not None and len(self.pending) > 0:
            raise Exception("Can't do multiple concurrent scans if pending")
        self.pending = list()
        for dongle in self.__dongles.itervalues():
            logger.debug("%s scanning" % dongle.dbus_path)
            dongle.scan()
            self.pending.append(dongle.dbus_path)
    
    def __rotate_dongle(self):
        '''
        Internal method used for concurrent scan, each time each one of the
        scanners completets it's work this method gets called until there
        are no more dongles in the sequence.
        When that happens we tell the server we're done.
        '''
        self.__index += 1
        if self.__index >= len(self.__sequence):
            self.tellListenersAsync(CYCLE_COMPLETE)
            self.__index = 0
            logger.debug('ScanManager dongle cycle completed')
            return True
        logger.debug('ScanManager dongle rotated, dongle: %s' % self.__sequence[self.__index])
        return False

    def __getScannerForPath(self, path):
        '''
        Translate dbus path to scanner device
        '''
        for dongle in self.__dongles.itervalues():
            if dongle.dbus_path == path:
                return dongle
        raise Exception("Path not Valid")

    # signal callbacks      
    def device_found(self, address, values, path=None):
        '''
        This callback gets called when ever a device has been found over dbus.
        We add the result to our discovered buffer, so we then tell the server
        all the results together. With real discovery time.
        '''
        dongle = self.__getScannerForPath(path)
        if address not in dongle.found:
            dongle.found[address] = dict()
            dongle.found[address]['rssi'] = list()
            dongle.found[address]['time'] = list()
            
        if 'name' not in dongle.found[address] and 'Name' in values:
            dongle.found[address]['name']=smart_str(values['Name'])
        if  'devclass' not in dongle.found[address] and 'Class' in values:
            dongle.found[address]['devclass'] = int(values['Class'])
        
        dongle.found[address]['rssi'].append(int(values['RSSI']))
        dongle.found[address]['time'].append(time.time())
        logger.debug(
                '%s device found: %s, %s' % (
                                                path, 
                                                address, 
                                                values.get('Name', None)
                                            )
                    )
        
    def property_changed(self, name, value, path=None):
        '''
        Callback that will let us know when a scan cycle has been completed,
        or started.
        '''
        if self.__index == None:
            return
        if name=='Discovering':
            if value==0:
                logger.debug('Discovery completed for path: %s' % path)
                dongle = self.__getScannerForPath(path)
                dongle.endScan()
                if self.concurrent and dongle.dbus_path in self.pending:
                    self.pending.remove(dongle.dbus_path)
                self.discovery_completed(dongle)
                return
            else:
                logger.debug('Discovery started for path: %s' % path)
                return
        logger.debug("property_changed %s %s %s" % (name, value, path) )
    
    def exposed_cycleCompleted(self):
        '''
        Exposed method that lets the server know if our scan cycle is done.
        '''
        return self.__index == len(self.__sequence) - 1
            
    def discovery_completed(self, dongle):
        '''
        This method gets called once the scan cycle is done, or all the 
        concurrent scanners have done they're job. This is when we send
        the server all our results. And tell we're done for a new scan
        cycle
        '''
        founds = list()
        
        if dongle.found:
            for found,data in dongle.found.iteritems():
                founds.append(
                    { 
                    'address': str(found), 
                    'name': smart_str(data.get('name', None)),
                    'rssi': data['rssi'],
                    'time': data['time'],
                    'devclass': int(data.get('devclass',-1))
                    }
                )

        addr=str(dongle.bt_address)
        
        if len(founds) > 0:
            self.tellListenersAsync(FOUND_DEVICE, 
            address=str(dongle.bt_address),
            records=ByValWrapper(founds) )
        
        if not self.concurrent:
            ret=self.__rotate_dongle()
            if not ret:
                self.tellListenersAsync(
                    CYCLE_SCAN_DONGLE_COMPLETED,
                    address=addr
                )
        elif len(self.pending) == 0:
            self.tellListenersAsync(CYCLE_COMPLETE)

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
    
    manager=ScanManager(dbus.SystemBus())
    manager.remote_listener=listen
    manager.scanners['00:50:C2:7F:EF:FE']=1
    
    gobject.threads_init()
    dbus.glib.init_threads()
    loop=gobject.MainLoop()
    manager.exposed_startScanningCycle()
    loop.run()

