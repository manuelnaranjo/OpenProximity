import os

__all__ = ['write', 'read']

def write(name, content):
    '''
	Try to send data to a pipe, if non one is listening then we just drop it
    '''
    if name not in write.pipes:
	try:
	    fp = os.open(name, os.O_NONBLOCK|os.O_WRONLY)
	    write.pipes[name] = fp
	except:
	    # no one there yet, drop it
	    return
    try:
	os.write(write.pipes[name], content)
    except:
	# reader is gone, drop it
	return
write.pipes = {}

def read(name, buffer_length=4096):
    '''
	Try to read from a pipe, if there's no writer then, prevent failure
    '''
    if name not in read.pipes:
	try:
	    fp = os.open(name, os.NONBLOCK|os.ORONLY)
	    read.pipes[name] = fp
	except:
	    # no writer yet
	    return ''
    try:
	return os.read(read.pipes[name], buffer_length)
    except:
	# writer is gone
	return ''
read.pipes = {}
