#!/usr/bin/python
#testing pairing service

import gobject

import sys, os
import dbus, dbus.service, dbus.mainloop.glib
from net.aircable.utils import logger, logmain

if __name__ == '__main__':
    logmain("pair.py")

PIN=os.environ.get("PIN_CODE", "1234")
logger.info("PIN code defaulting to %s" % PIN)

class Rejected(dbus.DBusException):
	_dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):
	exit_on_release = True

	def set_exit_on_release(self, exit_on_release):
		self.exit_on_release = exit_on_release

	@dbus.service.method("org.bluez.Agent",
					in_signature="", out_signature="")
	def Release(self):
		logger.info("Agent Release")
		if self.exit_on_release:
		    logger.info("Exiting from loop")
		    mainloop.quit()

	@dbus.service.method("org.bluez.Agent",
					in_signature="os", out_signature="")
	def Authorize(self, device, uuid):
	    logger.info("Authorize (%s, %s)" % (device, uuid))

	@dbus.service.method("org.bluez.Agent",
					in_signature="o", out_signature="s")
	def RequestPinCode(self, device):
	    logger.info("RequestPinCode (%s): %s" % (device, PIN) )
	    return PIN

	@dbus.service.method("org.bluez.Agent",
					in_signature="o", out_signature="u")
	def RequestPasskey(self, device):
	    logger.info("RequestPasskey (%s): %s" % (device, PIN) )
	    return dbus.UInt32(PIN)

	@dbus.service.method("org.bluez.Agent",
					in_signature="ou", out_signature="")
	def DisplayPasskey(self, device, passkey):
	    logger.info("DisplayPasskey (%s, %d)" % (device, passkey))

	@dbus.service.method("org.bluez.Agent",
					in_signature="ou", out_signature="")
	def RequestConfirmation(self, device, passkey):
	    logger.info("RequestConfirmation (%s, %d)" % (device, passkey))
	    if passkey == PIN:
		logger.info("passkey matches")
		return
	    logger.info("passkey doesn't match")
	    raise Rejected("Passkey doesn't match")

	@dbus.service.method("org.bluez.Agent",
					in_signature="s", out_signature="")
	def ConfirmModeChange(self, mode):
	    logger.info("ConfirmModeChange (%s)" % (mode))

	@dbus.service.method("org.bluez.Agent",
					in_signature="", out_signature="")
	def Cancel(self):
	    logger.info("Cancel")

def create_device_reply(device):
	logger.info("New device (%s)" % (device))
	mainloop.quit()

def create_device_error(error):
	logger.info("Creating device failed: %s" % (error))
	mainloop.quit()

if __name__ == '__main__':
    try:
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	bus = dbus.SystemBus()
	manager = dbus.Interface(bus.get_object("org.bluez", "/"),
							"org.bluez.Manager")

	if len(sys.argv) > 1:
		path = manager.FindAdapter(sys.argv[1])
	else:
		path = manager.DefaultAdapter()

	adapter = dbus.Interface(bus.get_object("org.bluez", path),
							"org.bluez.Adapter")

	path = "/test/agent"
	agent = Agent(bus, path)

	mainloop = gobject.MainLoop()

	if len(sys.argv) > 2:
		if len(sys.argv) > 3:
			device = adapter.FindDevice(sys.argv[2])
			adapter.RemoveDevice(device)

		agent.set_exit_on_release(False)
		adapter.CreatePairedDevice(sys.argv[2], path, "DisplayYesNo",
					reply_handler=create_device_reply,
					error_handler=create_device_error)
	else:
		adapter.RegisterAgent(path, "DisplayYesNo")
		logger.info("Agent registered")

	mainloop.run()
	logger.info("Agent is exiting")
	#adapter.UnregisterAgent(path)
	#print "Agent unregistered"
    except Exception, err:
	logger.error("Something went wrong on the agent application")
	logger.exception(err)


