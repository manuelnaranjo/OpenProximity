#!/usr/bin/python
# -*- coding: utf-8 -*-
#testing pairing service

import gobject

import sys, os
import dbus, dbus.service, dbus.mainloop.glib
from net.aircable.utils import logger
import rpyc

DEFAULT_PIN=os.environ.get("PIN_CODE", "1234")
logger.info("PIN code defaulting to %s" % DEFAULT_PIN)
server = None

PATH="/net/aircable/pairing"

def connect(address, port):
    logger.info("Connecting to %s:%s" % (address, port))
    try:
      s = rpyc.connect(address, int(port))
      return s
    except Exception, err:
      logger.error("can't connect to server")
      logger.exception(err)
    return None

def getPIN(address, dongle):
  global server
  print sys.argv
  if len(sys.argv) > 2:
    logger.info("server available")
    if not server:
      logger.info("server available")
      server=connect(sys.argv[1], sys.argv[2])
    try:
      out = server.root.getPIN(address, dongle)
      return str(out)
    except Exception, err:
      logger.error("couldn't get PIN from server")
      logger.exception(err)
  logger.info("faulting to default pin")
  return DEFAULT_PIN

def handle_name_owner_changed(own, old, new):
    if own.startswith('org.bluez'):
	if new is None or len(str(new))==0:
	    logger.info( "bluez has gone down, time to get out")
	else:
	    logger.info( "bluez started, time to restart")
	

def registerAgent(path):
    adapter = dbus.Interface(bus.get_object("org.bluez", path),
						  "org.bluez.Adapter")
    adapter.RegisterAgent(PATH, "DisplayYesNo")
    logger.info("adapter registered for path %s" % path)


def handle_adapter_added(path, signal):
    logger.info("bluez.%s: %s" % (signal, path))
    registerAgent(path)

def handle_adapter_removed(path, signal):
    logger.info("adapter removed %s" % path)

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
	def RequestPinCode(self, path):
	    device = dbus.Interface(bus.get_object("org.bluez", path),
							"org.bluez.Device")
	    dongle = dbus.Interface(bus.get_object("org.bluez", 
					      device.GetProperties()['Adapter']),
					"org.bluez.Adapter")
	    device=str(device.GetProperties()['Address'])
	    dongle=str(dongle.GetProperties()['Address'])
	    print device, dongle
	    pin=getPIN(device, dongle)
	    logger.info("RequestPinCode (%s->%s): %s" % (dongle, device, pin) )
	    return pin

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
	    device = dbus.Interface(bus.get_object("org.bluez", device),
							"org.bluez.Device")
	    dongle = dbus.Interface(bus.get_object("org.bluez", 
					      device.GetProperties()['Adapter']),
					"org.bluez.Adapter")
	    device=str(device.GetProperties()['Address'])
	    dongle=str(dongle.GetProperties()['Address'])
	    print device, dongle
	    pin=getPIN(device, dongle)
	    if passkey == pin:
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

def registerControlSignals(bus):
    bus.add_signal_receiver(handle_name_owner_changed,
	'NameOwnerChanged',
	'org.freedesktop.DBus',
	'org.freedesktop.DBus',
	'/org/freedesktop/DBus')

    bus.add_signal_receiver(handle_adapter_added,
	signal_name='AdapterAdded',
	dbus_interface='org.bluez.Manager',
	member_keyword='signal')

    bus.add_signal_receiver(handle_adapter_removed,
	signal_name='AdapterRemoved',
	dbus_interface='org.bluez.Manager',
	member_keyword='signal')

def initAgent():
    try:
	manager = dbus.Interface(bus.get_object("org.bluez", "/"),
							"org.bluez.Manager")
	for path in manager.ListAdapters():
	  registerAgent(path)
	logger.info("Agent registered on all paths")
    except Exception, err:
	logger.error("Something went wrong on the agent application")
	logger.exception(err)

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    registerControlSignals(bus)
    mainloop = gobject.MainLoop()
    agent = Agent(bus, PATH)
    agent.set_exit_on_release(False)
    initAgent()
    mainloop.run()
    logger.info("Agent is exiting")
