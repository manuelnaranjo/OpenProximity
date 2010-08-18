'''
Created on 31/05/2010

@author: manuel
'''

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

