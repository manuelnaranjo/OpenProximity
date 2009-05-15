import dbus
import const
import utils

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
		utils.logger.debug("Initializated Adapter(%s, %s)" % (self, self.is_aircable)) 

	def __str__(self):
		return '%s, %s' % (self.bt_address, self.dbus_path)

if __name__=='__main__':
	import dbus.glib
	import gobject
	adapter = Adapter( dbus.SystemBus(),'/org/bluez/hci0')
	print adapter, adapter.aircable
 