# -*- coding: utf-8 -*-
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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

from lxml import etree
from re import compile
from exceptions import IOError

from net.aircable.utils import getLogger
logger = getLogger(__name__)

VALID_ADDRESS=compile("([0-9a-f]{2}\:){5}([0-9a-f]{2})")

DEFAULT='''<xml>
<dongle>
</dongle>
</xml>'''

class XMLTool:
    """
    In [1]: from lxmltool import XMLTool

    In [2]: xt = XMLTool()

    In [3]: tree = xt.getXmlTree()

    In [4]: type(tree)
    Out[4]: <type 'lxml.etree._ElementTree'>

    In [5]: xt.getAdminPasswd()
    Out[5]: 'secret\n    '

    In [6]: xt.getAd
    xt.getAdminEmail   xt.getAdminName    xt.getAdminPasswd  

    In [6]: xt.getAdminName()
    Out[6]: 'x-ip\n    '

    In [7]: xt.getAdminEmail()
    Out[7]: 'foo@bar.com\n    '
    """
    
    def __init__(self, xmlfile="/etc/openproximity/settings.xml"):
        self.__file = xmlfile
        self.tree = None

    def __getXmlTree(self):
        """ Open an xml file and return an etree xml instance or None
        """
        self.tree = etree.parse(self.__file)
        if self.tree is None:
            raise Exception("no config file")
        
    def __sanitize(self):
        try:
            if self.tree is None:
                self.__getXmlTree()
        except Exception, err:
            logger.info("failed while loading file settings, trying to simulate"
                    " config file")
            logger.exception(err)
            self.tree=etree.fromstring(DEFAULT)

    def __getValueOrDefault(self, key, default):
        self.__sanitize()
        try:
            return self.tree.xpath(key)[0].text
        except:
            # if we got here then it's quite possible there's no 
            # setting defined in the xml
            return default

    #persistance methods
    def getAllSettings(self):
        return {
                'admin':{
                    'name': self.getAdminName(),
                    'password': self.getAdminPasswd(),
                    'email': self.getAdminEmail()
                },
                'logo': self.getLogo(),
                'debug': self.isDebugEnabled(),
                'translate': self.isTranslateEnabled(),
                'dongles': self.getAllDonglesSettings()
        }

    def genXML(self, settings, indent=1, header="xml"):
        out = ""
        if header:
            out+="<%s>\n" % header
        for key, value in settings.iteritems():
            for i in range(indent):
                out+="\t"
            out+="<%s>" % key
            if type(value) is dict:
                out+="\n%s\n" % self.genXML(value, indent+1, None)
                for i in range(indent):
                    out+="\t"
                out+="</%s>\n" % key

            else:
                out+=str(value)
                out+="</%s>\n" % key
        if header:
            out+="</%s>" % header

        return out
        
    def saveSettings(self, settings):
        out = file(self.__file, 'w')
        out.write(self.genXML(settings))
        out.close()
        
    # generic functions
    def getValueOrDefault(self, key, default=None):
        """Generic return function"""
        return self.__getValueOrDefault(key, default)
        
    def getDict(self, parent, default={}):
        """Generic access to dict values"""
        self.__sanitize()
        key = self.tree.findall(parent)
        if len(key) > 0:
            return self.__todict(key[0], False)
        return default

    # Admin stuff...
    def getAdminPasswd(self, default="aircable"):
        """ Return the admin password set in the xml file as string or None
        """
        return self.__getValueOrDefault('admin/password', default)

    def getAdminName(self, default="admin"):
        """ Return the admin name set in the xml file as string or None
        """
        return self.__getValueOrDefault('admin/name', default)

    def getAdminEmail(self, default="foo@foo.com"):
        """ Return the admin email set in the xml file as string or None
        """
        return self.__getValueOrDefault('admin/email', default)
            
    # logo staff ...
    def getLogo(self, default='logo.gif'):
        """ Return the path to the logo file as string
        """
        return self.__getValueOrDefault('logo', default)

    # debug staff
    def isDebugEnabled(self, default="true"):
        """Return debug preference as configured in xxx.xml
        """
        debug = self.__getValueOrDefault('debug', default)
        return debug.lower() == "true"

    def isTranslateEnabled(self, default="true"):
        """Return translate preference as configured in xxx.xml
        """
        translate = self.__getValueOrDefault('translate', default)
        return translate.lower() == "true"

    # dongle stuff ...
    def getAllDonglesSettings(self):
        try:
            self.__sanitize()
            blocks = self.tree.findall('dongle/block')
            out = dict()
            for block in blocks:
                addr = block.find('address').text
                out[addr]=self.__todict(block)

            # back to default
            default = self.tree.findall('dongle/default')
            if len(default) > 0:
                out['default'] = self.__todict(default[0])
            return out
        except AttributeError:
            return {}
    
    def getSettingsByAddress(self, address=""):
        """
        In [1]: from lxmltool import XMLTool

        In [2]: xt = XMLTool()

        In [3]: xt.getSettingsByAddress()
        Out[3]: {}

        In [4]: xt.getSettingsByAddress('f4:50:C2:00:00:02')
        Out[4]: {'scanner': ['1', 'True'], 'uploader': ['1', 'False']}

        In [5]: dic = xt.getSettingsByAddress('f4:50:C2:00:00:02')

        In [6]: dic
        Out[6]: {'scanner': ['1', 'True'], 'uploader': ['1', 'False']}

        In [7]: dic['scanner']
        Out[7]: ['1', 'True']

        In [8]: dic['uploader']
        Out[8]: ['1', 'False']
        
        # if the address doesnt exist, return default values declared in the
        # xml file
        In [9]: xt = XMLTool()

        In [9]: xt.getSettingsByAddress('f4:50:C2:00:00:06')
        Out[9]: {'scanner': ['1337', 'False'], 'uploader': ['20', 'True']}

        """
        
        if not VALID_ADDRESS.match(address.lower()):
            raise Exception("Not Valid Bluetooth Address %s" % address)
        try:
            self.__sanitize()

            blocks = self.tree.findall('dongle/block')
            for block in blocks:
                addr = block.find('address').text.lower()
                if address.lower().startswith(addr):
                    logger.info("%s passes filter %s" %( address, addr))
                    return self.__todict(block)

            # back to default
            default = self.tree.findall('dongle/default')
            if len(default) > 0:
                block = default[-1]
                return self.__todict(block)
            
            # not even default settings
            return {}
            
        except AttributeError:
            return {}

    def __todict(self, block, ignore_address=True):
        out = dict()
        for children in list(block):
            if children.tag!='address' or not ignore_address:
                if len(list(children)) > 0:
                    out[children.tag] = self.__todict(children, ignore_address)
                else:
                    out[children.tag]=children.text
        return out

if __name__ == '__main__':
    print "using foo.xml"
    xt = XMLTool("foo2.xml")

    print '00:50:C2:00:00:02', xt.getSettingsByAddress('00:50:C2:00:00:02')
    print 'f4:AA:BB:00:00:06', xt.getSettingsByAddress('f4:AA:BB:00:00:06')
    print xt.getAdminName()
    print xt.getAdminPasswd()
    print xt.getAdminEmail()
    set = xt.getAllSettings()
    print set
    print xt.genXML(set)

