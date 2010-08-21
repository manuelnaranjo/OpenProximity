# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net

'''
Database wrapper for ssh remote management system
'''

import sqlite3
from time import time
from base64 import encodestring, decodestring
import os

DATABASE_NAME=os.environ.get('DATABASE_NAME', "/tmp/remotecontrol.db") 
conn = sqlite3.connect(DATABASE_NAME)
conn.row_factory = sqlite3.Row

__all__=[
     'getConfigKeyValue', 'setConfigKeyValue', 'delConfigKey', # configuration 
     'isUserEnabled', 'enableUser', 'disableUser', # user
            'createUser', 'deleteUser',
            'updateUserLastLogin', 'updateUserName', 'updateUserAccumulatedTime' 
            'getUser', 'getAllUsers', 
        ]

def __generic_table_check(cur=None, configuration=None, table=None, 
                          create_text=None):
    broken = {}
    for key in configuration:
        broken[key]=True
    
    for row in cur.execute("pragma table_info(%s)" % table).fetchall():
        key = row['name']
        target = configuration[key]
        if target[0] == row['type'] and target[1] == bool(row['notnull']):
            broken[key] = False
        else:
            print "broken column", key

    flag=False
    for k in broken: 
        if broken[k]: 
            flag=True
    
    if flag:
        print "creating %s table" % table
        cur.execute("drop table if exists %s" %table)
        cur.execute('''create table %s ( %s );''' % (table, create_text))
        return True
    return False

def check_configuration_table(cur):
    configuration={'key': ('text', True), 
                   'value': ('text', True)} #coded database schema
    table="configuration"
    create_text="key text not null unique, value text not null"
    return __generic_table_check(cur, configuration=configuration, table=table,
                                 create_text=create_text)

def check_user_table(cur):
    configuration={'rsa_key': ('text', True),
                   'user': ('text', True),
                   'lastlogin': ('integer', True),
                   'enabled': ('boolean', False),
                   'accumulated_time': ('integer', True),
                } #coded database schema
    table="users"
    create_text='''rsa_key text not null unique,
                    user text not null,
                    lastlogin integer not null, 
                    enabled boolean default false,
                    accumulated_time integer not null default 0'''
    return __generic_table_check(cur, configuration=configuration, table=table,
                                 create_text=create_text)
    

def sanitize():
    c = conn.cursor()
    
    check_configuration_table(c)
    check_user_table(c)
    conn.commit()
    print "database is ready"
    
    c.close()
    
### configuration functions
def getConfigKeyValue(key):
    c = conn.cursor()
    c.execute("SELECT value FROM configuration where key=?", (key,))
    ret = c.fetchone()
    if ret: ret=ret[0]
    c.close()
    return ret

def setConfigKeyValue(key, value):
    c = conn.cursor()
    
    if getConfigKeyValue(key):
        c.execute("UPDATE configuration SET value=? where key=?;", (value, key))
    else:    
        c.execute("INSERT INTO configuration values (?,?)", (key, value))
    conn.commit()
    c.close()

def delConfigKey(key):
    c = conn.cursor()
    c.execute("DELETE FROM configuration WHERE key=?", (key,))
    conn.commit()
    c.close()


### user functions
def __user_dict(value):
    value = dict(value)
    if 'key' in value:
        value['key'] = decodestring(value['key'])
    return value

def isUserEnabled(key):
    c = conn.cursor()
    key=encodestring(key)
    res=c.execute("SELECT enabled as enabled FROM users WHERE rsa_key=?", (key,)).fetchone()
    c.close()
    if not res or len(res)==0: return False
    return bool(res['enabled'])

def getUser(username=None, key=None):
    c = conn.cursor()
    
    qs = '''SELECT 
                rsa_key AS key,
                user AS user,
                DATETIME(lastlogin,'unixepoch') AS lastlogin,
                lastlogin AS unix_time,
                enabled AS enabled,
                accumulated_time AS accumulated_time
                FROM users'''

    if (key and username) or not (key or username):
        raise Exception("Need username or rsa_key to do a user lookup, not both") 

    if key:
        key=encodestring(key)
        res=c.execute(qs+ " WHERE rsa_key=?", (key,)).fetchall()
    elif username:
        print "getUser, username:", username
        res=c.execute(qs+ " WHERE user=?", (username,)).fetchall()
    
    c.close()
    
    if not res or len(res)==0:
        return None
    if key:
        return __user_dict(res[0])
    return [__user_dict(x) for x in res]

def createUser(key=None, username=None, lastlogin=None, enabled=False):
    c = conn.cursor()
    print type(key)
    lastlogin=lastlogin or time()
    key=encodestring(key)
    c.execute('''
        INSERT INTO users values (?, ?, ?, ?, 0)''',
              (key, username, lastlogin, enabled))
    conn.commit()
    c.close()

def updateUserLastLogin(key=None, last_login=None):
    c = conn.cursor()
    key=encodestring(key)
    last_login=last_login or time()
    c.execute('''
        UPDATE users 
        SET lastlogin=? 
        WHERE rsa_key=?''',
              (last_login, key))
    conn.commit()
    c.close()
    
def updateUserName(key=None, username=None):
    c = conn.cursor()
    key=encodestring(key)
    c.execute('''
        UPDATE users 
        SET user=? 
        WHERE rsa_key=?''',
              (username, key))
    conn.commit()
    c.close()
    

def enableUser(key=None):
    c = conn.cursor()
    key=encodestring(key)
    c.execute('''
        UPDATE users 
        SET enabled=1 
        WHERE rsa_key=?''',
              (key,))
    conn.commit()
    c.close()

def disableUser(key=None):
    c = conn.cursor()
    key=encodestring(key)
    c.execute('''
        UPDATE users 
        SET enabled=0 
        WHERE rsa_key=?''',
              (key,))
    conn.commit()
    c.close()

def updateUserAccumulatedTime(key=None):
    c = conn.cursor()
    key=encodestring(key)
    user=list(getUser(key=key))[0]
    last_login=int(user['unix_time'])
    now = time()
    elapsed=now-last_login
    c.execute('''
                UPDATE users 
                SET accumulated_time=? 
                WHERE rsa_key=?''',
                  (elapsed, key))
    conn.commit()
    c.close()
    
    
def deleteUser(key):
    c = conn.cursor()
    key=encodestring(key)
    c.execute("DELETE FROM users WHERE rsa_key=?", (key,))
    conn.commit()
    c.close()

def getUsers():
    c = conn.cursor()
    
    qs = '''SELECT 
                rsa_key AS key,
                user AS user,
                DATETIME(lastlogin,'unixepoch') AS lastlogin,
                lastlogin AS unix_time,
                enabled AS enabled,
                accumulated_time AS accumulated_time
 
                FROM users'''

    res=c.execute(qs).fetchall()

    c.close()
    
    for result in res:
        yield __user_dict(result)

sanitize()
