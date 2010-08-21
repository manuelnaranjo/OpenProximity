# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net

'''
config management for remote forward only ssh server
'''

import default_config
import database

__NEEDS_LOADING=True

config=dict()

if __NEEDS_LOADING:
    for k in dir(default_config):
        if k.startswith('__'):
            continue
        u = database.getConfigKeyValue(k)
        default, convert = getattr(default_config, k) 
        if not u:
            config[k] = default
        else:
            config[k] = convert(u)
            
    __NEEDS_LOADING=False
