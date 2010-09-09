# -*- coding: utf-8 -*-
import socket as sk
import gobject
import errno
from threading import Thread
try:
    from net.aircable.utils import logger
except:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

class StreamServer():
    def __init__(self, interface, portnumber):
	self.interface = interface
	self.portnumber = portnumber
	self.clientsockets = {}

    def stop(self):
	for client in self.clientsockets.itervalues():
	    client.close()
	self.socket.close()

    def create_server_socket(self):
	logger.info("Creating stream socket %s" % self.portnumber)
	s = sk.socket(sk.AF_INET, sk.SOCK_STREAM, 0)
	s.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
	s.setblocking(False)
	s.bind((self.interface, self.portnumber))
	s.listen(128)
	flag = 0
	for f in dir(gobject):
	    if f.startswith('IO_'):
		print f
		flag |= getattr(gobject, f)
	gobject.io_add_watch(s.fileno(), flag, self.connection_ready)
	logger.info("Stream Server ready")
	self.socket = s

    def send_to_all(self, text, mimetype='text/plain'):
	delete = []
	for client in self.clientsockets:
	    try:
		s = self.clientsockets[client]
		s.sendall('--myboundary\r\n')
		s.sendall('Content-type: %s\r\n' % mimetype)
		s.sendall('Content-size: %s\r\n' % len(text))
		s.sendall('\r\n')
		s.sendall(text)
		s.sendall('\r\n')
	    except sk.error, err:
		logger.info("%s:%s got disconnected" % client)
		logger.error(err)
		s.close()
		delete.append(client)
	logger.info("sent to %s clients" % (len(self.clientsockets)-len(delete)))
	for d in delete:
	    del self.clientsockets[d]

    def handle_connection(self, conn, remote):
      request = conn.recv(4096)
      conn.setblocking(0)
      command, url = request.splitlines()[0].split()[:2]
      if command.strip() != 'GET':
	conn.shutdown(sk.SHUT_RDWR)
	conn.close()
	return True

      if url.strip() != '/':
	conn.shutdown(sk.SHUT_RDWR)
	conn.close()
	return True

      logger.info("Got a connection to the http stream, redirecting")
      host = ''
      for line in request.splitlines():
        if line.find('Host')>-1:
    	    host=line.strip().split()[1].split(':', 1)[0]

      conn.sendall('HTTP/1.0 200 OK\r\n')
      conn.sendall('Content-type:multipart/x-mixed-replace; boundary=--myboundary\r\n')
      conn.sendall('\r\n')
      self.clientsockets[remote] = conn
      logger.info("Connection ready for streamming")
      return True


    def connection_ready(self, sock, condition):
      while True:
        try:
    	    logger.info("connection ready")
    	    conn, remote = self.socket.accept()
    	    #sock.listen(1)
    	    logger.info("accepted")
    	    self.handle_connection(conn, remote)
        except sk.error, e:
    	    logger.error(e)
    	    if e[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
    		raise
    	    return True


if __name__ == '__main__':
    from time import time
    b = StreamServer('', 10000)
    b.create_server_socket()
    def say_hello(b):
	print "saying hello"
	b.send_to_all("%s Hello world\n" % time())
	return True
    gobject.timeout_add(1000, say_hello, b)
    b = gobject.MainLoop()
    b.run()
