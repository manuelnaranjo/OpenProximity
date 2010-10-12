#!/usr/bin/python
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


'''
An advanced pairing manager that will connect to OpenProximity rpc server in to
ask which PIN code to use.

SPP mode not yet supported.
'''

import gobject

import sys, os
import dbus, dbus.service, dbus.mainloop.glib
from net.aircable.utils import logger
import rpyc

DEFAULT_PIN=os.environ.get("PIN_CODE", "1234")
# default pin to use when no server is available.

logger.info("PIN code defaulting to %s" % DEFAULT_PIN)
server = None

PATH="/net/aircable/pairing"
# Path where we register our pairing agent.

def connect(address, port):
  '''
    This method wraps rpyc server connection, so when no server is available 
    the pairing manager will still work.
  '''
  logger.info("Connecting to %s:%s" % (address, port))
  try:
    s = rpyc.connect(address, int(port))
    return s
  except Exception, err:
    logger.error("can't connect to server")
    logger.exception(err)
  return None

def getPIN(address, dongle):
  '''
  This method will try to ask the server which PIN code to use, otherwise 
  fallback to the default PIN.
  '''
  global server
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
  '''
  When ever bluez goes up or down we will get called, we don't register here 
  though, we do it on handle_adapter_added as that's when we know which dongles
  are available.
  '''
  if own.startswith('org.bluez'):
      if new is None or len(str(new))==0:
	  logger.info( "bluez has gone down, time to get out")
      else:
	  logger.info( "bluez started, time to restart")
	

def registerAgent(path):
  '''
  Register an agent on the given dbus path.
  '''
  adapter = dbus.Interface(bus.get_object("org.bluez", path),
						"org.bluez.Adapter")
  adapter.RegisterAgent(PATH, "NoInputNoOutput") 
  # should we change this to NoInputNoOutput?
  logger.info("adapter registered for path %s" % path)


def handle_adapter_added(path, signal):
  '''
  When ever a new dongle is attached, or bluez starts a signal is generated, 
  that's when we register the agent for that adapter.
  '''
  logger.info("bluez.%s: %s" % (signal, path))
  registerAgent(path)

def handle_adapter_removed(path, signal):
  '''
  When ever a dongle is removed we will get notified, as we only run with one
  agent instance we have nothing to do.
  '''
  logger.info("adapter removed %s" % path)

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
  exit_on_release = True

  def set_exit_on_release(self, exit_on_release):
    self.exit_on_release = exit_on_release

  @dbus.service.method("org.bluez.Agent", in_signature="", out_signature="")
  def Release(self):
    '''
    Release the agent, and exit the loop. Gets called by BlueZ when it needs us
    to release the agent.
    '''
    logger.info("Agent Release")
    if self.exit_on_release:
	logger.info("Exiting from loop")
	mainloop.quit()

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
    This method gets called when the service daemon needs to get the passkey for
    an authentication.

    The return value should be a string of 1-16 characters length. The string 
    can be alphanumeric.
    '''
    device = dbus.Interface(bus.get_object("org.bluez", path), 
							"org.bluez.Device")
    dongle = dbus.Interface(bus.get_object("org.bluez", 
				      device.GetProperties()['Adapter']),
				"org.bluez.Adapter")
    device=str(device.GetProperties()['Address'])
    dongle=str(dongle.GetProperties()['Address'])
    pin=getPIN(device, dongle)
    logger.info("RequestPinCode (%s->%s): %s" % (dongle, device, pin) )
    return pin

  @dbus.service.method("org.bluez.Agent", in_signature="o", out_signature="u")
  def RequestPasskey(self, device):
    '''
    This method gets called when the service daemon needs to get the passkey for
    an authentication.

    The return value should be a numeric value between 0-999999.
    '''
    logger.info("RequestPasskey (%s): %s" % (device, PIN) )
    return dbus.UInt32(PIN)

  @dbus.service.method("org.bluez.Agent", in_signature="ou", out_signature="")
  def DisplayPasskey(self, device, passkey):
    '''
    This method gets called when the service daemon needs to display a passkey 
    for an authentication.

    The entered parameter indicates the number of already typed keys on the 
    remote side.

    An empty reply should be returned. When the passkes needs no longer to be 
    displayed, the Cancel method of the agent will be called.

    During the pairing process this method might be called multiple times to 
    update the entered value.
    '''
    logger.info("DisplayPasskey (%s, %d)" % (device, passkey))

  @dbus.service.method("org.bluez.Agent", in_signature="ou", out_signature="")
  def RequestConfirmation(self, device, passkey):
    '''
    This method gets called when the service daemon needs to confirm a passkey 
    for an authentication.

    To confirm the value it should return an empty reply or an error in case the
    passkey is invalid.
    '''
    logger.info("RequestConfirmation (%s, %d)" % (device, passkey))
    device = dbus.Interface(bus.get_object("org.bluez", device),
						"org.bluez.Device")
    dongle = dbus.Interface(bus.get_object("org.bluez", 
				      device.GetProperties()['Adapter']),
				"org.bluez.Adapter")
    device=str(device.GetProperties()['Address'])
    dongle=str(dongle.GetProperties()['Address'])
    pin=getPIN(device, dongle)
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
    This method gets called to indicate that the agent  request failed before a
    reply was returned.
    '''
    logger.info("Cancel")

def registerControlSignals(bus):
  '''
  Register our selves with some important dbus signals.
  '''
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
  '''
  Initialize the agent, register with every available path if possible.
  '''
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
