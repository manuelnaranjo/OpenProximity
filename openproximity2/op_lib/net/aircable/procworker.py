# Written by Naranjo Manuel Francisco <manuel@aircable.net>

"""Worker queues for Python (also called thread pools).

This class queues work and distributes it over a set of slave process. The
slaves are Callable instances that get called in their own process. 

The enqueue() function is used to queue function calls.

"""
import multiprocessing, functools
from multiprocessing import Lock, Semaphore
from net.aircable.utils import logger

__all__=['Manager', 'Lock', 'Semaphore']

class Worker(multiprocessing.Process):
    def __init__(self, id, manager, queue, out, semaphore, *args, **kwargs):
	multiprocessing.Process.__init__(self,*args,**kwargs)
	self.id = id
	self.manager = manager
	self.queue = queue
	self.running = False
	self.out=out
	self.semaphore=semaphore

    def run(self):
	# takes an element from the queue and process it
	while [ 1 ]:
	    func, args, kwargs = self.queue.get(True)
	    self.running = True
	    logger.debug("got func from queue")

	    # make the call the manager has all ready make sure this
	    # call is a partial
	    kwargs['out']=self.out
	    kwargs['semaphore']=self.semaphore
	    func(*args,**kwargs)

	    # allow others to know we're free again
	    self.running = False

    def busy(self):
	return self.running

class Manager(object):
    '''A class that manages subprocess calls'''

    def __init__(self, pids=7):
	self.queue = multiprocessing.Queue()
	self.out = multiprocessing.Queue()
	self.semaphore = multiprocessing.Semaphore()
	self.workers = [ Worker( b, self, self.queue, self.out, self.semaphore ) for b in range(0,pids) ]

    def put(self, function, *args, **kwargs):
#	part = functools.partial(function, *args, **kwargs)
	self.queue.put([function, args, kwargs])
	
    def put_out(self, *args, **kwargs):
	self.out.put([args,kwargs])
	
    def get_out(self):
	return self.out.get(True)

    def running_count(self):
	i = 0
	for j in self.workers:
	    if j.busy(): i+=1
	return i
	
    def start(self):
	for j in self.workers:
	    j.start()

    def stop(self):
	self.queue.close()
	self.queue.join_thread()
	self.out.close()
	self.out.join_thread()
	for j in self.workers:
	    j.terminate()

if __name__=='__main__':
    def do_work(val):
	print val
	
    import time
    from random import randint
    # tester
    b=Manager(10)
    print "manager created"

    print "added to queue"
    b.start()
    
    for k in range(0,100):
	b.put(do_work, k)
	time.sleep(randint(0,200)*.001)
    
    print "stopping"
    b.stop()
