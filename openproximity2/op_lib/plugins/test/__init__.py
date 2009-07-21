# an example base plugin
provides = { 
    'name': 'TEST plugin', 		# friendly name
    
    'django': True,			# expose me as a django enabled plugin
    
    'TEMPLATE_DIRS': 'templates',	# static media I give to django
    'LOCALE_PATHS': 'locale',
    
    'INSTALLED_APPS': 'test',		# we provide a hole application
    
    'urls': ( 'test', 'urls' )		# <server>/test points to my urls
}
