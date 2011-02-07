#	OpenProximity2.0 is a proximity marketing OpenSource system.
#	Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation version 2 of the License.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License along
#	with this program; if not, write to the Free Software Foundation, Inc.,
#	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


from openproximity.models import Setting
#from BeautifulSoup import BeautifulSoup
from dojo_util import json_encode, json_decode
import urllib, httplib, urllib2, cookielib
import models

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)

class AgentSettings():
    __defaults = {
	'server':   (str, None), # key: (type, default)
	'hash_id':   (str, None),
	'password': (str, None),
	'enabled':  (bool, False),
	'cron_minute': (str, None),
	'cron_hour': (str, None),
	'cron_dom': (str, None),
	'cron_month': (str, None),
	'cron_dow': (str, None),
    }
    @classmethod
    def __check_boolean(klass, value):
        if value and type(value) == str:
    	    if value.lower() not in ['true', 'false']:
	        raise ValueError, "Can't convert to boolean %s" % value


    @classmethod
    def getSetting(klass, key, default=None):
	if key not in klass.__defaults:
	    raise Exception('Not valid key: %s, valid options are: %s' % (key, klass.__defaults.keys()))
	set = klass.__defaults[key]
	if Setting.objects.filter(name='agent2_%s' % key).count()>0:
	    s = Setting.objects.get(name='agent2_%s' % key)
	    return set[0](s.value)
	if key=='enabled':
	    klass.__check_boolean(default)
	return set[0](default) if default else set[1]

    @classmethod
    def setSetting(klass, key, value=None):
	if key not in klass.__defaults:
	    raise Exception('Not valid key: %s, valid options are: %s' % (key, klass.__defaults.keys()))
	if key=='enabled':
	    klass.__check_boolean(value)
	set, created = Setting.objects.get_or_create(name='agent2_%s' % key)
	set.value=klass.__defaults[key][0](value)
	set.save()
	return set.value

getSetting = AgentSettings.getSetting
setSetting = AgentSettings.setSetting

def getLockOverRecords(klass):
    pks=[p[0] for p in klass.objects.filter(flag=False).values_list('pk')]
    klass.objects.filter(pk__in=pks).update(flag=True)
    return pks

def getRecordsForUpload(klass, pks):
    return klass.objects.filter(pk__in=pks).values_list(*klass.fields)

def getRemotesForUpload(klass, pks):
    return klass.objects.filter(pk__in=pks).values_list('record__remote__address')[0]

def unlockRecords(klass, pks):
    return klass.objects.filter(pk__in=pks).update(flag=False)

def deleteRecords(klass, pks):
    return klass.objects.filter(pk__in=pks).delete()

def get_csrf_token(klass):
    req = urllib2.Request(
	'%s/%s?csrf_token=True' % (getSetting('server'), klass.apiurl),
    )
    return json_decode(urllib2.urlopen(req).read())['csrf_token']

def pushRecords(klass, records, remotes):
    data = json_encode({
        'hash_id': getSetting('hash_id'),
        'password': getSetting('password'),
        'remotes': remotes,
        'records': klass.values_to_dict(records),
    })
    headers = {
	"Content-Type": "application/json",
	"Accept": "application/json",
	"X-Requested-With": "XMLHttpRequest"
    }
    print '%s/%s' % (getSetting('server'), klass.apiurl)
    conn = httplib.HTTPConnection(getSetting('server').replace("http://", ""))
    conn.request('POST', '/%s' % klass.apiurl, body=data, 
	headers=headers)
    r=conn.getresponse()
    content=r.read()
    conn.close()
    print r.status, r.reason
    print content
    if r.status in range(200, 299):
	return int(content.split()[1])
    print content
    raise Exception("failed reason: %s" % r.reason)

def doGenericRecords(klass):
    pks = getLockOverRecords(klass)
    if len(pks) == 0:
	return 0

    records = getRecordsForUpload(klass, pks)
    remotes = getRemotesForUpload(klass, pks)
    amount = pushRecords(klass, records, remotes)

    print "Commited %i out of %i" % (amount, len(pks))

    if amount!=len(pks):
	unlockRecords(klass, pks)
	raise Exception, "didn't commit all the records, commit %i out of %i" % (amount, len(pks))
    deleteRecords(klass, pks)
    return amount

def doRecordsAndLog():
    scan = 0
    sdp = 0
    success = True
    try:
	scan=doGenericRecords(models.uploadFoundRecord)
    except Exception, err:
	success=False
	print err

    try:
	sdp=doGenericRecords(models.uploadSDPRecord)
    except Exception, err:
	success=False
	print err

    models.UploadRecord( commited_scan_records = scan,
	commited_sdp_records = sdp,
	success = success).save()
    return success

def test_connection(server, hash_id, password, *args, **kwargs):
    data = {
        'hash_id': hash_id,
        'password': password,
    }
    data = urllib.urlencode(data)
    print server, '%sapi/test_credentials/' % server
    print data
    req = urllib2.Request(
	'%sapi/test_credentials/' % server,
	data,
    )
    response = urllib2.urlopen(req)
    response=response.read()
    return response.split()[1].lower()=='true'
