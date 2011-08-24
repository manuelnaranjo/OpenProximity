from net.aircable.utils import logger
from threading import Timer
from time import time

class Task:
    def internal_callback(self):
        logger.debug("Timer timeout %s" % self)
        self.callback(*self.a, **self.kw)
        self.dispatcher.cueue.remove(self)
    
    def cancel(self):
        logger.info("Timer.cancel %s" % self)
        self.dispatcher.cueue.remove(self)
        self.timer.cancel()

    def __init__(self, dispatcher, delay, callback, *a, **kw):
        assert type(delay) is float or int
        assert callable(callback)
        logger.info("new Timer %s %f %s" % (self, delay, callback))
        self.dispatcher = dispatcher
        self.callback = callback
        self.a = a
        self.kw = kw
        self.timer = Timer(delay, self.internal_callback)
        self.timer.start()

class Dispatcher():
    cueue = []

    def callLater(self, delay, callback, *a, **kw):
        t = Task(self, delay, callback, *a, **kw)
        self.cueue.append(t)
        return t

    def cancelCallLater(self, task):
        if task in self.cueue:
            task.cancel()
            return True
        return False

    def cancelAll(self):
        for task in self.cueue:
            task.cancel()
        self.cueue = []

if __name__ == '__main__':
    import sys
    t1=t2=t3=None
    dispatcher = Dispatcher()
    def task1():
        print time(), "task1 completed"
        sys.exit(0)
    
    def task2(*a, **kw):
        print time(), "task2 completed", a, kw
    
    def task3():
        print time(), "task3 completed"
    
    def task4(dispatcher, t):
        print time(), "task4 completed", t, dispatcher.cancelCallLater(t)
    
    t1=dispatcher.callLater(10, task1)
    t2=dispatcher.callLater(1, task2, "hello world", a=1, b=2, c=3)
    t3=dispatcher.callLater(11, task3)
    dispatcher.callLater(4, task4, dispatcher, t3)
    dispatcher.callLater(2, task4, dispatcher, None)
    dispatcher.callLater(3, task4, dispatcher, t2)
    print time(), "started"
