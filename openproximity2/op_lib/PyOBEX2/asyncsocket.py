A#! /bin/python

import socket, bluetooth, gobject, errno, select
from re import compile

BTERR=compile('\((?P<errno>\d+)\,.*\)')

class BluetoothAsyncSocket(bluetooth.BluetoothSocket):
	# registered watchs with gobject
	watch = list()

	# class variables
	__callback = None 
		# holder for a succesful callback, it's up to the user app
		# to know why it got called
	__err_callback = None 
		# holder for an error callback, the FSM is set by the
		# user code.
	read_buffer=""
	__read_ready = None
		# if you want to get informed when there's data ready to be readed
		# on the buffer add this callback

	def __init__(self, *args, **kwargs):
		bluetooth.BluetoothSocket.__init__(self, *args, **kwargs)
		self.setblocking(False)

	def setCallback(self, callback):
		self.__callback = callback

	def setErrCallback(self, callback):
		self.__err_callback = callback

	def setReadReady(self, callback):
		self.__read_ready = callback

	def callback(self, *args, **kwargs):
		if callable(self.__callback):
			self.__callback(*args, **kwargs)

	def err_callback(self, *args, **kwargs):
		if callable(self.__err_callback):
			self.__err_callback(*args, **kwargs)

	def read_ready(self, *args, **kwargs):
		if callable(self.__read_ready):
			self.__read_ready(*args, **kwargs)

	def connect(self):
		raise Exception("Don't use this function, use connect_ex instead")

	def remove_callbacks(self):
		for i in self.watch:
		    gobject.source_remove(i)
		self.watch=list()

	def __connected(self, source, condition):
		self.remove_callbacks()

		self.watch.append(
			gobject.io_add_watch(
				self, 
				gobject.IO_ERR | gobject.IO_HUP, 
				self.__connection_lost
			)
		)

		self.watch.append(
			gobject.io_add_watch(
				self, 
				gobject.IO_IN, 
				self.__data_received
			)
		)

		self.callback()
		return False

	def __data_received(self, source, condition):
		self.read_buffer+=bluetooth.BluetoothSocket.recv(self, 0xffff)
		self.read_ready(len(self.read_buffer))
		return True

	def __connection_lost(self, source, condition):
		print "__connection_lost"
		self.remove_callbacks()
		err = self.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
		if err != 0:
		    self.err_callback(err)
		else:
		    self.err_callback(errno.ENOTCONN)
		return False

	def connect_ex(self, target, callback=None, err_callback=None,*args, **kwargs):
		assert callable(callback), "callback needs to be callable"
		assert callable(err_callback), "err_callback needs to be callable"
		self.__callback=callback
		self.__err_callback=err_callback

		err=bluetooth.BluetoothSocket.connect_ex(self, target, *args, **kwargs)
		if err != errno.EINPROGRESS:
			print "something failed, errno", err, errno.errorcode[err]
			self.err_callback(err)
			return

		self.watch.append(
			gobject.io_add_watch(
				self, 
				gobject.IO_ERR | gobject.IO_HUP, 
				self.__connection_lost
			)
		)

		self.watch.append(
			gobject.io_add_watch(
				self, 
				gobject.IO_OUT, 
				self.__connected
			)
		)

		return True


	def recv(self, length, flags=0, *args, **kwargs):
		if len(self.read_buffer) >= length:
			out = self.read_buffer[:length]
			self.read_buffer=self.read_buffer[length:]
			print "pending", len(self.read_buffer)
			return out
		if flags and socket.MSG_WAITALL:
			raise Exception("Not yet ready")
		out = self.read_buffer
		self.read_buffer=""
		return out

def init():
	gobject.threads_init()

if __name__ == '__main__':
	loop=gobject.MainLoop()
	loop.run()
