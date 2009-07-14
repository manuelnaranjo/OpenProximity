"""
    A simple class for creating spp servers.

    Copyright 2008 Wireless Cables Inc. <www.aircable.net>
    Copyright 2008 Naranjo, Manuel Francisco <manuel@aircable.net>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import socket
import dbus

from errors import *
from sppBase import *
from xml.dom.minidom import parseString

class sppServer(sppBase):
	__RecHandle = 0
	
	def __init__(self, 
		    channel=1, 
		    service='spp', 
		    device = None):
	    sppBase.__init__(self, channel, service, device);
	    self.logInfo("sppServer.__init__")
	    

	def listenAndWait(self):
	    '''
		Waits for the connection, and initialziates the connections.
		
		It is recommened that you all ready have an sdp record registered
		before calling this method, and that you remove it as soon as this
		method ends.
		
		This method will block.
	    '''
	    if (self.__RecHandle <= 0):
		self.logWarning("No SDP service registered");
		
	    self.logDebug( 'creating socket' )
	    sock = socket.socket( socket.AF_BLUETOOTH, 
						socket.SOCK_STREAM, 
						socket.BTPROTO_RFCOMM );
	    #Let BlueZ decide outgoing port
	    self.logDebug ( 'binding to %s, %i' % ( self.device , self.channel ) )
	    sock.bind( (self.device,self.channel) );

	    self.logDebug ( 'Listening' )
	    sock.listen( 1 );
	    
	    self.logInfo ( 'Waiting for connection' )
	    (self.socket, self.peer) = sock.accept()
	    
	    self.logInfo( 'Connection from %s at channel %s' % 
		(self.peer[0], self.peer[1]) )
		
	    sock.close()
	    
	def __registerSDPOldAPI(self, xml):
	    self.logWarning("BlueZ 3.X API doesn't allow to register records on just one specific device")
	    obj = self.bus.get_object('org.bluez', '/org/bluez')
	    self.database = dbus.Interface(obj, 'org.bluez.Database')
	    self.__RecHandle = self.database.AddRecordFromXML(xml)
	    
	def __registerSDPNewAPI(self, xml):
	    self.database = dbus.Interface(self.getAdapterObjectPath(),
				'org.bluez.Service');
	    self.__RecHandle = self.database.AddRecord(xml)
	    
	def __genXML(self, name, description):
	    return '''
<?xml version=\"1.0\" encoding=\"UTF-8\" ?>

		<record>
        <attribute id=\"0x0000\">
                <uint32 value=\"0x00010001\" />
        </attribute>
        <attribute id=\"0x0001\">
                <sequence>
                        <uuid value=\"0x1101\" />
                </sequence>
        </attribute>
        <attribute id=\"0x0004\">
                <sequence>
                        <sequence>
                                <uuid value=\"0x0100\" />
                        </sequence>
                        <sequence>
                                <uuid value=\"0x0003\" />
                                <uint8 value=\"0x%X\" />
                        </sequence>
                </sequence>
        </attribute>
        <attribute id=\"0x0005\">
                <sequence>
                        <uuid value=\"0x1002\" />
                </sequence>
        </attribute>
        <attribute id=\"0x0006\">
                <sequence>
                        <uint16 value=\"0x656e\" />
                        <uint16 value=\"0x006a\" />
                        <uint16 value=\"0x0100\" />
                </sequence>
        </attribute>
        <attribute id=\"0x0009\">
                <sequence>
                        <sequence>
                                <uuid value=\"0x1101\" />
                                <uint16 value=\"0x0100\" />
                        </sequence>
                </sequence>
        </attribute>
        <attribute id=\"0x0100\">
                <text value=\"%s\" />
        </attribute>
        <attribute id=\"0x0101\">
                <text value=\"%s\" />
        </attribute>
</record>''' % (self.channel, name, description )
	    
	
	def registerSDP(self, name="sppServer",  
				description="AIRcable SensorSDK SPP Server",
				xml_entry=None):
	    '''
		Registers the SDP record with the SDP database
		
		Arguments (all optionals):
		    name: Name for the service when you want sppServer to generate
			    xml sdp record
		    description: Description for the service when you want sppServer to generate
			    xml sdp record
		    xml_entry: If you are not going to use spp then you need to provide
			    this argument
	    '''
	    self.logInfo("Registering service %s named %s with description %s" %
		    (self.service, name, description) )
		    
	    if self.service != 'spp' and not xml_entry:
		raise SPPNotImplemented, "If you are not going to use spp then you need to provide the xml record"
	
	    if self.service == 'spp':
		xml = self.__genXML(name, description)
	    else:
		xml = xml_entry
		
	    self.logDebug( "Registering:%s" % xml )
	    
	    if self.new_bluez_api :
		self.__registerSDPNewAPI(xml)
	    else:
		self.__registerSDPOldAPI(xml)
	    
	    self.logInfo( "Registered, RecHandle = 0x%X" % self.__RecHandle )
	    
	def unregisterSDP(self):
	    if self.__RecHandle < 0:
		raise SPPException, "Can't unregister SDP record if it wasn't registered first"
	    
	    self.logInfo("Removing SDP record handle: 0x%X" % self.__RecHandle)
	    self.database.RemoveRecord(self.__RecHandle)


if __name__ == '__main__':
    import sys
    
    if ( '--help' in sys.argv ):
	print "Usage %s [<service> <channel> <adapter>]" % (sys.argv[0])
	sys.exit(1)
    
    if ( len(sys.argv) > 1):
	serv = sys.argv[1]
    else:
	serv = 'spp'
    
    if ( len(sys.argv) > 2 ):
	chan = sys.argv[2]
    else:
	chan = 1
    
    if ( len(sys.argv) > 3 ):
	dev = sys.argv[3]
    else:
	dev = None
	
    a = sppServer(
	    channel	=chan,
	    service	=serv,
	    device	=dev
	);
    
    a.registerSDP()
    a.listenAndWait()
    a.unregisterSDP()
    
    print a.readLine()
    a.sendLine('How are you?')
    print a.readLine()
    
    a.disconnect()
