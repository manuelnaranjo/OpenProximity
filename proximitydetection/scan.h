/*
 *  Proximity scanning command line application, this is based on a bluez 
 * 	example [1]. 
 * 	With callbacks functions and all what's needed to get a fully working 
 * 	bluetooth proximity system. 
 * 
 *  To build this get into Debug and run make.
 *
 *  If it fails then you need to do:
 *  rm ../marshal.c
 *  rm ../marshal.h (make sure you don't delete marshal.list)
 *  glib-genmarshal --prefix=marshal marshal.list --header > marshal.h
 *  glib-genmarshal --prefix=marshal marshal.list --body > marshal.c
 *  gcc `pkg-config --libs --cflags glib-2.0 dbus-1 dbus-glib-1` bluetooth.c \
 * 		marshal.c -o bluetooth
 * 
 *  Copyright (C) 2007  Naranjo Manuel Francisco <manuel@aircable.net>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 *  [1] http://wiki.bluez.org/wiki/HOWTO/DiscoveringDevices
 * 
 */

#ifndef SCAN_H_
#define SCAN_H_

#include <stdlib.h>
#include <dbus/dbus.h>
#include <dbus/dbus-glib.h>
#include <glib-object.h>
#include <sys/time.h>
#include <string.h>
#include <stdio.h>

#include "marshal.h"

//remove definition to avoid getting messages from the proximityScanning framework
#define __SCAN_DEBUG

#ifdef __SCAN_DEBUG
#undef  G_LOG_DOMAIN
#define G_LOG_DOMAIN "scanner"
#else
#undef g_message
#define g_message(...) ;
#endif

#define SCAN_OK	   						0
#define SCAN_ERROR 						1
#define SCAN_COMPLETED				  	2
#define	SCAN_ERROR_PERIODIC_DISCOVERY 	2 | SCAN_ERROR
#define SCAN_ERROR_NOT_STOPPED			4 | SCAN_ERROR
#define	SCAN_ERROR_NAME_RESOLVE			6 | SCAN_ERROR
#define	SCAN_ERROR_DONGLE_REMOVED		8 | SCAN_ERROR

#define SCAN_TRUE	1
#define SCAN_FALSE	0

//Amount of elements to store in the buffer
#define BUFFER_SIZE		100

// Timeout we consider for a device to tell if it has been discovered twice.
#define SCAN_TIMEOUT 	30

typedef struct _proximityScanner proximityScanner;

//public application loop
static GMainLoop *loop = NULL;

/**
 * Public functions
 */
void startScan(proximityScanner * scanner);
void stopScan(proximityScanner * scanner);
void run_mainloop (void);
/*
 * proximityScanner *initScanner(const char * hci): Returns a pointer to the 
 * 		structure and initializates what's needed, if hci is NULL then it will
 * 		use the default bluetooth dongle.
 */
proximityScanner *initScanner(const char * hci);
void	destroyScanner(proximityScanner * scanner);
void 	initDBusConnection();
void 	closeDBusConnection();


/*
 * Public structure supposed to be used from outside.
 * 
 * Callback functions:
 * 		+ int deviceDiscovered(const char*): 
 * 			Register for this function callback if you want to be noticed each 
 * 			time a new device is discovered. timeout will be considered here.
 * 			If the name of the device needs to be resolved, then return 
 * 			different from 0.
 * 			After this code gets the control back, it will free addr.
 * 		+ void nameResolved (const char* addr, const char* name):
 * 			Will be called as soon as the name for addr has been resolved.
 * 			After this code gets the control back, it will free addr and name.
 * 		+ void scanError(int errNumber):
 * 			When there's an error in the scan this callback will be called,
 * 			from this moment on, the state of the code is unpredictable.
 * 		
 * 
 * Members:
 * 		+ adapter: 
 * 			The code might be able to work with multiple dongles in the feature, 
 * 			this field will give support for that.
 * 		+ buffer: 
 * 			Last discovered devices buffer. BlueZ reports that it has found the 
 * 			same device multiple times, and not just one as expected.
 * 			So we need a way to prevent this from annoying us. This buffer will
 * 			not be shared among the devices.
 * 			The buffer will be initializated by initScanner
 * 		+ timeout:
 * 			Numbers of seconds that we consider for a device to be discovered
 * 			twice.
 * 
 */


struct _proximityScanner {
	//callbacks
	int 	(* deviceDiscovered)(const char *btAddr);
	void 	(* nameResolved)(const char * btAddr, const char * name);
	void	(* scanError)(int errNumber);
	
	//members
	DBusGProxy *adapter;
	GHashTable *buffer;
	int timeout;
	
};



#endif /*SCAN_H_*/
