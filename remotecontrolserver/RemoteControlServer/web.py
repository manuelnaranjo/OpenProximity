# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.web import resource, proxy
from twisted.python import log
import database
from base64 import encodestring
from hashlib import md5
from conf import config
import cgi
from user import ForwardUser

from re import compile

ProxyClient_original_handleResposePart = proxy.ProxyClient.handleResponsePart

def ProxyClient_handleResponsePart(self, buffer):
    host, port = self.headers['host'].split(':')

    buffer = buffer.replace('href="/', 'href="/proxy_%s_%s/' % (host, port))
    buffer = buffer.replace('src="/', 'src="/proxy_%s_%s/' % (host, port))
    buffer = buffer.replace('url(/', 'url(/proxy_%s_%s/' % (host, port))
    buffer = buffer.replace('value="/', 'value="/proxy_%s_%s/' % (host, port))
    buffer = buffer.replace('popitup(\'/', 'popitup(\'/proxy_%s_%s/' % (host, port))
    ProxyClient_original_handleResposePart(self, buffer)

proxy.ProxyClient.handleResponsePart=ProxyClient_handleResponsePart

REDIRECT='''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 
   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
        <title>Remote Control Server - %(title)s</title>
        <meta HTTP-EQUIV="REFRESH" content="1; url=/">
    </head>
    <body>
        %(text)s
        <br/>
        Done, you will be redirected in 1 seconds
        <br/>
        <a href="/">Redirect me now</a>
    </body>
</html>
'''


class MainSite(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)

        self.putChild('user', UserManager())
        self.putChild('config', ConfigManager())
        self.putChild('status', StatusManager())
        # need to do this for resources at the root of the site
        self.putChild("", self)
        
    def getChild(self, name, request):
	if 'proxy_' in name:
	    host, port = name.split('_')[1:]
	    b = proxy.ReverseProxyResource(host, int(port), '')
	    return b
	
	return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
	StatusOutput=''
	for user in ForwardUser.loggedin:
	    for host, port in user.listeners:
		listener = user.listeners[(host, port)]
		StatusOutput+='''<tr>
		    <td>%(username)s</td>
		    <td>%(rhost)s:%(rport)s</td>
		    <td>%(host)s:%(port)s</td>
		    <td><a href="javascript:forward(%(port)s);">Open</a></td>
		    <td><a href="/proxy_localhost_%(port)s/">Proxy</a></td>
		</tr>''' % {
		    'username': user.username,
		    'rhost': listener.remote_host,
		    'rport': listener.remote_port,
		    'host': host,
		    'port':port
		}

        UserOutput=''
        for user in database.getUsers():
            key = md5(user['key']).hexdigest()
            UserOutput+="""<tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td><a href=\"/user/%s/\">Config</a></td>
            <td><a href=\"/user/%s/delete/\">Delete</a></td>
            </tr>""" % (
                            user['user'], 
                            "yes" if user['enabled'] else "no",  
                            key, 
                            user['lastlogin'], 
                            user['accumulated_time'],
                            user['id'],
                            user['id'])

        ConfigOutput=''
        for key, val in config.iteritems():
            ConfigOutput+="""
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td><a href=\"/config/%s/\">Config</a></td>
            </tr>""" % (key, val, key)

        out="""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 
   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
        <title>Remote Control Server</title>
	<script type="text/javascript">
	    function forward(port){
		var url = location.protocol+'//'+location.host.split(':')[0] + ':' + port;
		location.href=url
	    }
	</script>
    </head>
    <body>
	<h1>Status</h1>
	<table style=\"width:100%%;\">
	    <tr>
		<td>UserName</td>
		<td>Remote Port</td>
		<td>Local Port</td>
		<td></td>
	    </tr>
	    %s
	</table>
        <h1>Users</h1>
        <table style=\"width:100%%;\">
            <tr>
                <td>UserName</td>
                <td>Enabled</td>
                <td>RsaKey Md5</td>
                <td>Last Login</td>
                <td>Accumulated Time</td>
                <td></td>
                <td></td>
            </tr>
            %s
        </table>
        <h1>Configuration</h1>
        <table>
            <tr>
                <td>Key</td>
                <td>Value</td>
                <td></td>
            </tr>
            %s
        </table>
    </body>
</html>""" % (StatusOutput, UserOutput, ConfigOutput)
        return str(out)

class StatusManager(resource.Resource):
    def getChild(self, path, request):
        return ServerStatus(id=path)

    def render_GET(self, request):
        raise Exception("Not valid")

class ServerStatus(resource.Resource):

    def __init__(self, id):
        resource.Resource.__init__(self)
        self.id = id
        self.putChild('', self)
        
    def render_GET(self, request):
        return ''

class UserManager(resource.Resource):
    def getChild(self, path, request):
        return UserStatus(id=path)

    def render_GET(self, request):
        raise Exception("Not valid")

class UserStatus(resource.Resource):

    def __init__(self, id):
        resource.Resource.__init__(self)
        self.id = id
        self.user = database.getUserByID(id)
        self.user['checked']= "checked" if self.user['enabled'] else ''
        self.user['key']=encodestring(self.user['key'])
        self.putChild('', self)
        self.putChild('config', UserConfig(self.id))
        self.putChild('delete', DeleteUser(self.id))
        
    def render_GET(self, request):
        
        UserOut='''
            <tr>
                <td>UserName</td>
                <td><input name="user" type="text" value="%(user)s"/></td>
            </tr>
            <tr>
                <td>RSA Key</td>
                <td>%(key)s</td>
            </tr>
            <tr>
                <td>Enabled</td>
                <td><input name="enabled" type="checkbox" %(checked)s/></td>
            </tr>
            <tr>
                <td>Last Login</td>
                <td><input name="lastlogin" type="text" value="%(unix_time)s"/></td>
            </tr>
            <tr>
                <td>Accumulated Time</td>
                <td><input name="accumulated_time" type="text" value="%(accumulated_time)s"/></td>
            </tr>
        
        ''' % self.user
        out='''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 
   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
        <title>Remote Control Server - User Configuration</title>
    </head>
    <body>
        <h1>User %s</h1>
        <form action="config/" method="post">
            <table style=\"width:100%%;\">
            %s
            </table>
            <br/>
            <input type="submit" value="Save" />
            <input type="submit" name="delete" value="Delete" />
        </form>
    </body>
</html>''' % (self.user['user'], UserOut)
        return str(out)

class DeleteUser(resource.Resource):

    def __init__(self, id):
        resource.Resource.__init__(self)
        self.id = id
        self.user = database.getUserByID(id)
        self.putChild('', self)

    def render_GET(self, request):
	database.deleteUser(self.user['key'])
	return REDIRECT % {'title': "User Delete", 'text': "User has been Deleted"}

class UserConfig(resource.Resource):

    def __init__(self, id):
        resource.Resource.__init__(self)
        self.id = id
        self.user = database.getUserByID(id)
        self.putChild('', self)
    
    def render_POST(self, request):
        key=self.user['key']
        
        if 'delete' in request.args:
            return self.deleteUser()
        
        database.updateUserName(key, request.args['user'][0])
        
        if 'enabled' in request.args and request.args['enabled'][0].lower()=='on':
            database.enableUser(key)
        else:
            database.disableUser(key)
        
        database.updateUserLastLogin(key, request.args['lastlogin'][0])
        return REDIRECT % {'title': "User Updated", 'text': "User Updated"}
    
    def render_GET(self, request):
        return ""
    
    def deleteUser(self):
        database.deleteUser(self.user['key'])
        return REDIRECT % {'title': "User Delete", 'text': "User has been Deleted"}


class ConfigManager(resource.Resource):
    def getChild(self, path, request):
        return ConfigStatus(key=path)
    
    def render_GET(self, request):
        raise Exception("Not valid")

class ConfigStatus(resource.Resource):

    def __init__(self, key):
        resource.Resource.__init__(self)
        self.key = key
        self.value = config.get(key, None)
        self.putChild('', self)
        self.putChild('config', ConfigConfig(self.key))
        
    def render_GET(self, request):
        out='''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 
   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
        <title>Remote Control Server - Settings Configuration</title>
    </head>
    <body>
        <h1>Configuration</h1>
        <form action="config/" method="post">
            <table>
                <tr>
                    <td>Key</td>
                    <td><input type="text" name="key" value="%s" /></td>
                </tr>
                <tr>
                    <td>Value</td>
                    <td><input type="text" name="value" value="%s" /></td>
                </tr>
            </table>
            <br/>
            <input type="submit" value="Save" />
            <input type="submit" name="delete" value="Delete" />
        </form>
    </body>
</html>''' % (self.key, self.value)
        return str(out)

class ConfigConfig(resource.Resource):

    def __init__(self, key):
        resource.Resource.__init__(self)
        self.key = key
        self.putChild('', self)
    
    def render_POST(self, request):
        key=request.args['key'][0]
        value=request.args['value'][0]
        
        if 'delete' in request.args:
            return self.deleteSetting()
                
        database.setConfigKeyValue(key, value)
        return REDIRECT % {'title': 'Setting Updated', 'text': 'Setting has been updated'}

    def render_GET(self, request):
        return ""
    
    def deleteSetting(self):
        database.delConfigKey(self.key)
        return REDIRECT % {'title': 'Setting Deleted', 'text': 'Setting has been Deleted'}
