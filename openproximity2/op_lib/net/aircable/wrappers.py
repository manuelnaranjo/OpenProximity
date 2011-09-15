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
import dbus
import const
import utils
from net.aircable.utils import getLogger
logger=getLogger(__name__)

class Adapter(object):
    '''A wrapper arround an adapter'''
    dbus_path = None
    dbus_interface = None
    bt_address = None
    is_aircable = False
    bus = None

    def __init__(self, bus, path, name="OpenProximity 2.0"):
        self.dbus_path = path
        self.dbus_interface = dbus.Interface( bus.get_object(const.BLUEZ, path), const.BLUEZ_ADAPTER )
        #self.bt_address = self.dbus_interface.GetAddress()
        self.bt_address=str(self.dbus_interface.GetProperties()['Address'])
        self.dbus_interface.SetProperty('Powered', True)
        self.is_aircable = utils.isAIRcable(self.bt_address)
        self.bus = bus
        self.dbus_interface.SetProperty('Name', name)
        logger.debug("Initializated Adapter(%s, %s)" % (self, self.is_aircable)) 

    def __str__(self):
        return '%s, %s' % (self.bt_address, self.dbus_path)

if __name__=='__main__':
    import dbus.glib
    import gobject
    adapter = Adapter( dbus.SystemBus(),'/org/bluez/hci0')
    print adapter, adapter.aircable
