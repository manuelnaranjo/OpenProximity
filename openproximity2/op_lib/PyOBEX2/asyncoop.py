#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010 Naranjo Manuel Francisco <manuel@aircable.net>
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
#
# -*- coding: utf-8 -*-

from asyncsocket import BluetoothAsyncSocket, init

import common
from PyOBEX.common import OBEX_Version
from PyOBEX import requests, responses, headers
import struct
	
class Client(object):
	def __init__(self, callback=None, err_callback=None, loop=None):
	
		self.max_packet_length = 0xffff
		self.obex_version = OBEX_Version()
		self.__callback=callback
		self.__err_callback=err_callback
		self.loop = loop

		# internal state variables
		self.state = common.IDLE
		self.state_put = common.PUT_IDLE
		
		# internal holders
		self.pending_headers = []
		self.response_handler = responses.ResponseHandler()
		self.length = 0
		self.type = None
		self.invalid = False
		
		# a state flag that allow us to know if we have to send more
		# headers as soon as we get a reply		
		self.sending_headers = False
		
	def cleanup(self):
	    self.socket.remove_callbacks()
	    self.socket.close()
	
	def callback(self, *args, **kwargs):
		if self.invalid:
			return
		print "callback", args, kwargs
		if callable(self.__callback):
			self.__callback(self, *args, **kwargs)
	
	def err_callback(self, *args, **kwargs):
		print "err_callback", args, kwargs
		self.invalid = True
		if callable(self.__err_callback):
			self.__err_callback(self, *args, **kwargs)
			
	def internal_callback(self, *args, **kwargs):
		if self.state != common.PUT:
			return self.callback(*args, **kwargs)
			
		if self.state_put == common.PUT_HEADER:
			return self.put_headers_done(*args, **kwargs)
		
		if self.state_put == common.PUT_BODY:
			return self.put_body_done(*args, **kwargs)
			
		if self.state_put == common.PUT_FINAL:
			return self.put_done(*args, **kwargs)
			
		raise Exception("Invalid state %s %s" % (
												common.STATES[self.state],
												common.STATES_PUT[self.state_put]
						))
	
	def data_ready(self, amount):
		print "data_ready", amount
		if self.length == 0:
			if amount < 3:
				return
		
			format = ">BH"
			data = self.socket.recv(3)
			amount=amount-3
			type, length = struct.unpack(format, data)
		else:
			type = self.type
			length = self.length
		
		if length-3>amount:
			self.type = type
			self.length = length
			self.data = data
			print "pending data", length
			return
		data += self.socket.recv(length - 3)
		self.type = 0
		self.length = 0
		print type, length, len(data)
			
		if isinstance(self.request, requests.Connect):
			response = self.response_handler.decode_connection(type, length, data)
			self.remote_info = response
		else:
			response = self.response_handler.decode(type, length, data)
		
		if self.sending_headers and not isinstance(response, responses.Continue):
			self.err_callback(error=common.ObexError(response))
			return

		self.internal_callback(response=response)

	def __connected_rfcomm(self, *args, **kwargs):
		self.callback(*args[1:], **kwargs)
	
	def __failed_rfcomm(self, *args, **kwargs):
		self.err_callback(error=common.ErrnoError(args[0]), *args[1:], **kwargs)	

	def connect_rfcomm(self, address, port, callback, err_callback, bind=None):
		'''
			Start up the RFcomm level connection. Once this successed
			you have to call connect_rfcomm
		'''
		print "connecting rfcomm"
		self.socket = BluetoothAsyncSocket()
		self.__callback = callback
		self.__err_callback = err_callback
		if bind:
		    self.socket._sock.bind((bind, 0))
		self.socket.connect_ex((address, port), 
							callback=self.__connected_rfcomm, 
							err_callback=self.__failed_rfcomm)
		self.state = common.CONNECTING_RFCOMM
		return common.ReplyPending()
	
	def connect_obex(self, header_list=[]):
		'''
			Start the Obex connection.
		'''
		flags = 0
		data = (self.obex_version.to_byte(), flags, self.max_packet_length)

		max_length = self.max_packet_length
		request = requests.Connect(data)

		# upgrade our state
		self.state = common.CONNECTING_OBEX
		
		# register to get informed when more data is available
		self.socket.setReadReady(self.data_ready) 

		self.pending_headers = list(header_list)
		self._send_headers(request, max_length)

	def _send_headers(self, request, max_length):
	
		"""Convenience method to add headers to a request and send one or
		more requests with those headers."""
		
		while self.pending_headers:
		
			if request.add_header(self.pending_headers[0], max_length):
				self.pending_headers.pop(0)
			else:
				print "sending on headers", request.encode()
				self.socket.sendall(request.encode())
				request.reset_headers()
				self.sending_headers = True
				self.request = request
				# now we wait for data
				return common.ReplyPending
		
		self.sending_headers = False
		# Always send at least one request.
		if isinstance(request, requests.Get):
			# Turn the last Get request containing the headers into a
			# Get_Final request.
			request.code = requests.Get_Final.code
		
		print "sending", len(request.encode())
		self.socket.sendall(request.encode())
		self.request = request
		return common.ReplyPending
	
	def put_headers_done(self, response):
		if not isinstance(response, responses.Continue):
			return self.err_callback(common.ObexError(response))
		self.put_body()
		
	def put_body_done(self, response):
		if not isinstance(response, responses.Continue):
			return self.err_callback(common.ObexError(response))
		
		self.put_body()
		
	def put_done(self, response):
		if not isinstance(response, responses.Success):
			return self.err_callback(common.ObexError(response))
		
		self.callback(response)
		self.state = common.CONNECTED
		self.state_put = common.PUT_IDLE
		
		
	def put_body(self):
		max_length = self.remote_info.max_packet_length
		file_data = self.file_data
		
		# Send the file data.
		
		# The optimum size is the maximum packet length accepted by the
		# remote device minus three bytes for the header ID and length
		# minus three bytes for the request.
		optimum_size = max_length - 3 - 3
		
		data = file_data[:optimum_size]
		self.file_data=self.file_data[optimum_size:]
		
		if len(data) == 0:
			raise Exception("work done")
		
		if len(self.file_data) > 0:
			self.state_put = common.PUT_BODY
			request = requests.Put()
			request.add_header(headers.Body(data, False), max_length)
			self.socket.sendall(request.encode())			
		else:
			self.state_put = common.PUT_FINAL
			request = requests.Put_Final()
			request.add_header(headers.End_Of_Body(data, False), max_length)
			self.socket.sendall(request.encode())
	
	def put(self, name, file_data, header_list = ()):
		"""put(self, name, file_data, header_list = ())
		
		Sends a file with the given name, containing the file_data specified,
		to the server for storage in the current directory for the session,
		and returns the response.
		
		Additional headers can be sent by passing a sequence as the
		header_list keyword argument. These will be sent after the name and
		file length information associated with the name and file_data
		supplied.
		"""
		
		header_list = [
					headers.Name(name),
					headers.Length(len(file_data))
			] + list(header_list)
		
		max_length = self.remote_info.max_packet_length
		request = requests.Put()
		self.state = common.PUT
		self.state_put = common.PUT_HEADER
		
		self.file_data = file_data
		self.pending_headers = header_list
		
		self._send_headers(request, max_length)		
	
if __name__=='__main__':
	def callback(client, response=None, *args, **kwargs):
		if client.state == common.CONNECTING_RFCOMM:
			print "connected rfcomm", args, kwargs
			client.connect_obex()
		elif client.state == common.CONNECTING_OBEX:
			print "connected obex", client, response
			client.put(sys.argv[3], file(sys.argv[4], 'rb').read())
		elif client.state == common.PUT:
			print "uploaded completed"
			client.loop.quit()
		else:
			print "something completed", common.STATES[client.state], args, kwargs
		
	def error(client, error, *args, **kwargs):
		print "error", common.STATES[client.state], error, args, kwargs
		client.invalid = True
		client.loop.quit()
	
	import sys, gobject
	loop=gobject.MainLoop()
	client = Client(loop=loop)
	client.connect_rfcomm(sys.argv[1], int(sys.argv[2]), callback, error)
	
	init()
	if not getattr(client, 'invalid', False):
		loop.run()
	
