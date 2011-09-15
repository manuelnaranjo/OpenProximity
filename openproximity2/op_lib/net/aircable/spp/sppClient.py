"""
    A simple class for connecting to spp servers.

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
import net.aircable.sdp as sdp
import net.aircable.const as const

from net.aircable.utils import getLogger
logger=getLogger(__name__)

class sppClient(sppBase):
	target = None
	
	def __init__( self, target, 
                        channel = -1,
                        service = 'spp',
                        device  = None  ):
	    sppBase.__init__(self, 
			    channel = channel, 
			    service = service, 
			    device  = device);
	    logger.info("sppClient.__init__")
	    logger.info("target: %s" % target )
	    self.target = target


	def __browsexml(self, doc):
	    record=doc.documentElement
	    
	    for node in record.childNodes:
	        if node.nodeType == node.ELEMENT_NODE and node.getAttribute('id') == '0x0004':
			val = node.getElementsByTagName('uint8')
			return int(val[0].getAttribute('value'), 16)
				    
	def resolveService(self, target, service='spp' ):
	    logger.info("Resolving service %s for device %s...."
		    %(service, target) 
		);
	    
	    adapter = dbus.Interface( self.getAdapterObjectPath(), 
						    'org.bluez.Adapter' )
	    
	    return sdp.resolve(target, 
		uuid=const.UUID.get('spp', '00001101-0000-1000-8000-00805f9b34fb'),
		adapter=adapter, bus=self.bus)

	def connect(self):
	    '''
		Starts the connection
	    '''
	    logger.info("connecting")
	    if not self.target:
		raise SPPNotImplemented, 'Scanning is not supported, you need to do that by your own'
	    
	    if self.channel < 1:
		self.channel = self.resolveService( self.target, self.service)
		    
	    if (self.socket == None):
		logger.debug('creating socket')
		self.socket = socket.socket( getattr(socket, 'AF_BLUETOOTH', 31),
						socket.SOCK_STREAM, 
						getattr(socket, 'BTPROTO_RFCOMM', 3) );
	    #Let BlueZ decide outgoing port
	    logger.debug('binding to %s, %i' % ( self.device , 0 ))
	    self.socket.bind( (self.device,0) );
		
	    logger.debug('connecting to %s, %i' % ( self.target, self.channel ))
	    self.socket.connect( (self.target, self.channel) );


if __name__ == '__main__':
    import sys
    
    if ( len(sys.argv) < 2 ):
	print "Usage %s <target> [ <channel>  <adapter> ]" % (sys.argv[0])
	sys.exit(1)
    
    if ( len(sys.argv) > 2 ):
	chan = sys.argv[2]
    else:
	chan = -1
    
    if ( len(sys.argv) > 3 ):
	dev = sys.argv[3]
    else:
	dev = None
	
    a = sppClient(
	    target	=sys.argv[1],
	    channel	=chan,
	    service	='spp',
	    device	=dev
	);
    
    a.connect()
    
    a.sendLine('hi');
    print a.readLine();
    a.sendLine('bye');
                
    a.disconnect();
                    
