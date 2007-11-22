/*
 *
 *  DBus ObexFTP client.
 * 
 *  To build this get into Debug and run make.
 *
 *  If it fails then you need to do:
 *  rm ../marshal.c
 *  rm ../marshal.h (make sure you don't delete marshal.list)
 *  glib-genmarshal --prefix=marshal marshal.list --header > marshal.h
 *  glib-genmarshal --prefix=marshal marshal.list --body > marshal.c
 *  make
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
 */

#ifndef DBUSBINDING_H_
#define DBUSBINDING_H_

#include <obexftp/client.h>
#include <stdlib.h>
#include <dbus/dbus.h>
#include <dbus/dbus-glib.h>
#include <glib-object.h>
#include <glib/gstdio.h>
#include <sys/time.h>
#include <string.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <termios.h>


#include "marshal.h"

#define OBEX_TRANS_DBUS_BLUETOOTH OBEX_TRANS_CUSTOM

#define BUF_SIZE 1024

typedef struct _DBUS_BTData DBUS_BTData;

//callbacks for openobex
int DBUS_BTConnect(obex_t *handle, void * customdata);
int DBUS_BTDisconnect(obex_t *handle, void * customdata);
int DBUS_BTListen(obex_t *handle, void * customdata);
int DBUS_BTWrite(obex_t *handle, void * customdata, uint8_t *buf, int buflen);
int DBUS_BTHandleInput(obex_t *handle, void * customdata, int timeout);

void initDBusConnection();
void closeDBusConnection();
DBUS_BTData *initDBUS_BT(const char * addr, const char * service, const char * hci);
void initSerialService();
void openRFCommConnection(DBUS_BTData * data);

/* Internal Structure used for DBUS_BTData */
struct _DBUS_BTData{
	/* Internal Structure used for DBUS_BTData */
	DBusGProxy 	*hciProxy;
	char		*hciDev;
	char		*targetAddr;
	char	   	*service;
	char		*rfcommNode;
	FILE		*fd;
	char		*buffer;
};

#define __DBUS_BINDING_DEBUG

#endif /*DBUSBINDING_H_*/
