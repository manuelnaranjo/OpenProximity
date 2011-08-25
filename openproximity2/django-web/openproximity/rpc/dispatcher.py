try:
    from net.aircable.utils import logger
except:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("")

from threading import Timer, Thread, Event, Condition, Lock
import time
from time import time as now

class Task:
    def internal_callback(self):
        logger.debug("Timer timeout %s" % self)
        self.callback(*self.a, **self.kw)
        Dispatcher.cueue.remove(self)
    
    def cancel(self):
        logger.info("Timer.cancel %s" % self)
        Dispatcher.cueue.remove(self)

    def __init__(self, triggerTime, callback, *a, **kw):
        assert type(triggerTime) is float or int
        assert callable(callback)
        logger.info("new Timer %s %f %s" % (self, triggerTime, callback))
        self.callback = callback
        self.a = a
        self.kw = kw
        self.triggerTime = triggerTime

class Dispatcher(Thread):
    cueue = None
    instance = None
    cond = None
    nextTrigger = None

    def __init__(self):
        Thread.__init__(self)
        Dispatcher.instance = self
        Dispatcher.cueue = []
        self.cond = Condition(Lock())
        self.evt = Event()
    
    def run(self):
        while True:
            logger.debug("sleeping for %s" % self.nextTrigger)
            self.evt.wait(self.nextTrigger)
            n = now()
            tasks = [ b for b in Dispatcher.cueue if b.triggerTime <= n ]
            logger.debug("Doing %i callbacks" % len(tasks))
            for t in tasks:
                t.internal_callback()
            if len(Dispatcher.cueue) > 0:
                self.nextTrigger = min([b.triggerTime for b in Dispatcher.cueue]) - now()
            else:
                self.nextTrigger = None
            self.evt.clear()


    def __callLater(self, triggerTime, callback, *a, **kw):
        t = Task(triggerTime, callback, *a, **kw)
        Dispatcher.cueue.append(t)
        if not self.nextTrigger or triggerTime < self.nextTrigger:
            logger.debug("notifying condition")
            # we need to trigger before the next event
            self.evt.set()
            self.nextTrigger = triggerTime
        return t

    @classmethod
    def callLater(klass, triggerTime, callback, *a, **kw):
        return klass.instance.__callLater(triggerTime, callback, *a, **kw)

    @classmethod
    def cancelCallLater(klass, task):
        if task in klass.cueue:
            task.cancel()
            return True
        return False

    @classmethod
    def cancelAll(klass):
        for task in klass.cueue:
            task.cancel()
        klass.cueue = []
Dispatcher().start()

if __name__ == '__main__':
    import sys
    t1=t2=t3=None
    def task1():
        print now(), "task1 completed"
        sys.exit(0)
    
    def task2(*a, **kw):
        print now(), "task2 completed", a, kw
    
    def task3():
        print now(), "task3 completed"
    
    def task4(t):
        Dispatcher.callLater(now(), task2, "hello world", a=1, b=2, c=3)
        print now(), "task4 completed", t, Dispatcher.cancelCallLater(t)
    
    t1=Dispatcher.callLater(10+now(), task1)
    t2=Dispatcher.callLater(1+now(), task2, "hello world", a=1, b=2, c=3)
    t3=Dispatcher.callLater(11+now(), task3)
    Dispatcher.callLater(4+now(), task4, t3)
    Dispatcher.callLater(2+now(), task4, None)
    Dispatcher.callLater(3+now(), task4, t2)
    
    print now(), "started"
