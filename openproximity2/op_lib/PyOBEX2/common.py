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

import errno

# global FSM states 	
IDLE = 0
CONNECTING_RFCOMM = 1
CONNECTING_OBEX = 2
CONNECTED = 3
DISCONNECT = 4
DISCONNECTING = 5
PUT = 6
GET = 7

PUT_IDLE = 0
PUT_HEADER = 1
PUT_BODY = 2
PUT_FINAL = 3

STATES = {
		0: 'IDLE',
		1: 'CONNECTING_RFCOMM',
		2: 'CONNECTING_OBEX',
		3: 'CONNECTED',
		4: 'DISCONNECT',
		5: 'DISCONNECTING',
		6: 'PUT',
		7: 'GET',
}

STATES_PUT = {
		0: 'PUT_IDLE',
		1: 'PUT_HEADER',
		2: 'PUT_BODY',
		3: 'PUT_FINAL'
}

class error:
	def __init__(self, code):
		self.code = code

class ErrnoError(error):
	def __str__(self):
		return 'Errno error %s: %s' % (self.code, errno.errorcode[self.code])

class ObexError(error):
	def __str__(self):
		return "Obex Error %s" % self.code

class ReplyPending():
	pass

