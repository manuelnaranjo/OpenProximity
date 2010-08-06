# Modified by Manuel Naranjo for OpenProximity2 <manuel@aircable.net> 2009
# This autoreloader will reload on different events:
#	* RELOAD variable is TRUE (allowing incode reload)
#	* code changed
#	* SIGUSR1 is recieved
# Autoreloader will kill childs when parent dies
# sigusr1 to parent triggers parent killing
#
# Autoreloading launcher.
# Borrowed from Peter Hunt and the CherryPy project (http://www.cherrypy.org).
# Some taken from Ian Bicking's Paste (http://pythonpaste.org/).
#
# Portions copyright (c) 2004, CherryPy Team (team@cherrypy.org)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of the CherryPy Team nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os, sys, time, signal, threading
from net.aircable.utils import logger

__all__=['isParent', 'main', 'RESTART']

try:
    import thread
except ImportError:
    import dummy_thread as thread

# This import does nothing, but it's necessary to avoid some race conditions
# in the threading module. See http://code.djangoproject.com/ticket/2330 .
try:
    import threading
except ImportError:
    pass


RUN_RELOADER = True
RESTART = False

_mtimes = {}
_win = (sys.platform == "win32")

def isParent():
    '''
    This method will let the running process if it's the one that forked, or the
    forked one.
    '''
    if os.environ.get('DEBUG', None) is None:
	return os.getpid() == int(os.environ.get('RUN_PARENT', os.getpid()))
    else:
	return True

def handle_child(signum, frame):
    '''
    Gets called when a signal is received, by default we kill the child. The 
    parent will detect this and start a new child (when the return value was 3)
    '''
    sys.exit(3)
    
def handle_parent(signum, frame):
    '''
    When the parent gets the kill signal it will stop it self no forking more
    childrens.
    '''
    logger.info("Parent killed, doing exit")
    sys.exit(0)

def code_changed():
    '''
    An utility method that will check if there are any code changes in the inuse
    modules. When there's a change this method will return TRUE. Based on django
    code.
    '''
    global _mtimes, _win
    for filename in filter(lambda v: v, map(lambda m: getattr(m, "__file__", None), sys.modules.values())):
        if filename.endswith(".pyc") or filename.endswith(".pyo"):
            filename = filename[:-1]
        if not os.path.exists(filename):
            continue # File might be in an egg, so it can't be reloaded.
        stat = os.stat(filename)
        mtime = stat.st_mtime
        if _win:
            mtime -= stat.st_ctime
        if filename not in _mtimes:
            _mtimes[filename] = mtime
            continue
        if mtime != _mtimes[filename]:
            _mtimes = {}
            return True
    return False

def isRunning(pid):
    '''
    This method will inquiry PID to know if it's running.
    '''
    try:
	os.kill(pid, 0)
	return True
    except OSError, err:
	return False

def reloader_thread(t):
    '''
    This thread runs in the child. It will check if the parent is running, if
    so it will continue. If there's a change in the code, or if the worker 
    thread ended it will kill it self with signal 3.
    If no parent is available it will kill it self with error 0 (no parent, no
    way to restart)
    '''
    parent_pid=int(os.environ.get('RUN_PARENT'))
    while RUN_RELOADER:
	
	# check if parent is running
	if not isRunning(parent_pid):
	    # no parent, time to end
	    sys.exit(0)
	
        if code_changed() or RESTART or not t.isAlive():
            sys.exit(3) # force reload
        time.sleep(1)

def restart_with_reloader():
    '''
    This method will spawn a new child when the exit code is 3.
    '''
    while True:
        args = [sys.executable] + sys.argv
        if sys.platform == "win32":
            args = ['"%s"' % arg for arg in args]
        new_environ = os.environ.copy()
        new_environ["RUN_MAIN"] = 'true'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3:
            break;
    sys.exit(exit_code)

def python_reloader(main_func, args, kwargs):
    '''
    Internal method that will setup the forking process. If it's the parent
    then it will do the forks, otherwise it will start a new worker thread and
    setup a reloader thread.
    '''
    if os.environ.get("RUN_MAIN") == "true":
	signal.signal(signal.SIGUSR1, handle_child)
	t = threading.Thread(target=main_func, args=args, kwargs=kwargs)
	t.start()
        try:
            reloader_thread(t)
        except KeyboardInterrupt:
            pass
	except Exception, err:
	    logger.exception(err)
    else:
	# this is the parent pid
        try:
	    signal.signal(signal.SIGUSR1, handle_parent)
	    os.environ['RUN_PARENT']=str(os.getpid())
	    restart_with_reloader()
        except KeyboardInterrupt:
            pass

def main(main_func, args=(), kwargs={}):
    '''
    The only method you want to use from the outside, it will decide to use 
    either a forking schema when DEBUG is not defined. Or it will just call your
    method and don't fork at all, when you want to DEBUG.
    '''
    if os.environ.get('DEBUG', None) is None:
	python_reloader(main_func, args, kwargs)
    else:
	main_func(*args, **kwargs)

if __name__ == '__main__':
    def test():
	pass
    
    if isParent():
	print "I'm the parent:", os.getpid()
    else:
	print "I'm a child:", os.getpid()
    main(test)

    