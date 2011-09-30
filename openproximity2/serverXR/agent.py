# OpenProximity2.0 is a proximity marketing OpenSource system.
# Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


'''
OpenProximity pairing agent, this agent is ment to be run along our uploader
process.
'''
import gobject
import sys, os
import dbus, dbus.service
import rpyc

from net.aircable.utils import getLogger
logger = getLogger(__name__)

PATH="/net/aircable/agent"
# Path where we register our pairing agent.

bus = dbus.SystemBus()

class Rejected(dbus.DBusException):
    '''
    When the passkeys don't match BlueZ expects us to raise an exception.
    '''
    _dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):
    '''
    The passkey agent it self.
    
    Documentation for the methods come from BlueZ docs.
    '''

    def __init__(self, rpc_server, *a, **kw):
        self.rpc_server = rpc_server
        dbus.service.Object.__init__(self, *a, **kw)

    @dbus.service.method("org.bluez.Agent", in_signature="", out_signature="")
    def Release(self):
        '''
        Release the agent, and exit the loop. Gets called by BlueZ when it 
        needs us to release the agent.
        '''
        logger.info("Agent Release")

    @dbus.service.method("org.bluez.Agent", in_signature="os", out_signature="")
    def Authorize(self, device, uuid):
        '''
        This method gets called when the service daemon needs to authorize a 
        connection/service request.
        Don't raise any exception so BlueZ knows we accept.
        '''
        logger.info("Authorize (%s, %s)" % (device, uuid))

    @dbus.service.method("org.bluez.Agent", in_signature="o", out_signature="s")
    def RequestPinCode(self, path):
        '''
        This method gets called when the service daemon needs to get the 
        passkey for an authentication.

        The return value should be a string of 1-16 characters length. The 
        string can be alphanumeric.
        '''
        logger.info("request pin code")
        try:
	        device = dbus.Interface(bus.get_object("org.bluez", path), 
                            "org.bluez.Device")
	        dongle = dbus.Interface(bus.get_object(
		        "org.bluez", device.GetProperties()['Adapter']),
                                "org.bluez.Adapter")
	        device=str(device.GetProperties()['Address'])
	        dongle=str(dongle.GetProperties()['Address'])
	        pin=self.rpc_server.root.getPIN(device, dongle)
	        logger.info("RequestPinCode (%s->%s): %s" % (dongle, device, pin) )
	        return pin
        except Exception, err:
	        logger.error(err)
	        return "1234"

    @dbus.service.method("org.bluez.Agent", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        '''
        This method gets called when the service daemon needs to get the 
        passkey for an authentication.

        The return value should be a numeric value between 0-999999.
        '''
        logger.info("RequestPasskey")
        logger.info("RequestPasskey (%s): %s" % (device, PIN) )
        return dbus.UInt32(PIN)

    @dbus.service.method("org.bluez.Agent", in_signature="ou", out_signature="")
    def DisplayPasskey(self, device, value):
        '''
        This method gets called when the service daemon needs to display a 
        passkey for an authentication.

        The entered parameter indicates the number of already typed keys on the 
        remote side.

        An empty reply should be returned. When the passkes needs no longer to 
        be displayed, the Cancel method of the agent will be called.

        During the pairing process this method might be called multiple times 
        to update the entered value.
        '''
        logger.info("DisplayPasskey (%s, %s)" % (device, value))

    @dbus.service.method("org.bluez.Agent", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        '''
        This method gets called when the service daemon needs to confirm a 
        passkey for an authentication.

        To confirm the value it should return an empty reply or an error in 
        case the passkey is invalid.
        '''
        logger.info("RequestConfirmation (%s, %s)" % (device, passkey))
        device = dbus.Interface(bus.get_object("org.bluez", device),
                        "org.bluez.Device")
        dongle = dbus.Interface(bus.get_object("org.bluez", 
                            device.GetProperties()['Adapter']),
                "org.bluez.Adapter")
        device=str(device.GetProperties()['Address'])
        dongle=str(dongle.GetProperties()['Address'])
        pin=self.rpc_server.root.getPIN(device, dongle)
        if passkey == pin:
            logger.info("passkey matches")
            return
        logger.info("passkey doesn't match")
        raise Rejected("Passkey doesn't match")

    @dbus.service.method("org.bluez.Agent", in_signature="s", out_signature="")
    def ConfirmModeChange(self, mode):
        '''
        This method gets called if a mode change is requested that needs to be 
        confirmed by the user. An example would be leaving flight mode.
        '''
        logger.info("ConfirmModeChange (%s)" % (mode))

    @dbus.service.method("org.bluez.Agent", in_signature="", out_signature="")
    def Cancel(self):
        '''
        This method gets called to indicate that the agent  request failed 
        before a reply was returned.
        '''
        logger.info("Cancel")
