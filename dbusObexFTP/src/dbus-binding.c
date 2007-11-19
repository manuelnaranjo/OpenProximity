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

#include "dbus-binding.h"



//internal members
static DBusGConnection * dbusConnection = NULL;
static DBusGProxy* bzManager = NULL;
static DBusGProxy* sppManager = NULL;

static GMainLoop *loop = NULL;

//internal functions
static DBusGProxy* findAdapter(DBusGConnection * bus, const char * hci){
	GError *error = NULL;
	DBusGProxy * out = NULL;
	
	if (bzManager == NULL) {
		g_printerr("There's no connection to BlueZ so I can't continue\n");
		exit(EXIT_FAILURE);
	}
	
	if (hci == NULL){
		char * adapterStr;
	    if (!dbus_g_proxy_call (bzManager, "DefaultAdapter", &error, G_TYPE_INVALID,
	    		G_TYPE_STRING, &adapterStr, G_TYPE_INVALID)) {
	    	g_printerr ("Couldn't get default adapter: %s\n", error->message);
	    	exit(EXIT_FAILURE);
	    	return NULL;
	    }
	    
	    out = dbus_g_proxy_new_for_name(dbusConnection, "org.bluez", adapterStr, "org.bluez.Adapter");
		g_message ("Using: %s", adapterStr);
		g_free( adapterStr );
		
	} else {
		out = dbus_g_proxy_new_for_name(bus, "org.bluez", hci, "org.bluez.Adapter");
		g_message ("Using: %s", hci);
	}
	
	return out;
}


//external functions

void initDBusConnection(){
    GError *error = NULL;
    
    if (dbusConnection != NULL)
    	return;
    
    g_type_init();
    g_type_init_with_debug_flags (G_TYPE_DEBUG_OBJECTS);
    g_log_set_always_fatal (G_LOG_LEVEL_WARNING);
    loop = g_main_loop_new (NULL, FALSE);

    dbusConnection = dbus_g_bus_get(DBUS_BUS_SYSTEM, &error);
    if (error != NULL)
    {
    	//this is a serious error, we can't do anything if we can't connect to dbus
    	g_printerr("Connecting to system bus failed: %s\n", error->message);
    	g_error_free(error);
    	exit(EXIT_FAILURE);
    }
    
    g_message("Connected to DBUS");
    
    bzManager = dbus_g_proxy_new_for_name(dbusConnection, "org.bluez", 
			"/org/bluez", "org.bluez.Manager");
    
	if (bzManager == NULL) {
    	g_printerr("Couldn't connect to BlueZ manager.");
    	exit(EXIT_FAILURE);
    }
	
	g_message("Connected to BlueZ Manager");
	
	return;
}

void initSerialService() {
	char * conn;
	GError *error = NULL;
	
	if(bzManager == NULL) {
		g_printerr("You can't call initSerialService() before calling "
				"initDBUSConnection() sorry");
		exit(EXIT_FAILURE);
	}

    if (!dbus_g_proxy_call (bzManager, "ActivateService", &error, 
    		G_TYPE_STRING, "serial", G_TYPE_INVALID,
    		G_TYPE_STRING, &conn, G_TYPE_INVALID)) {
    	g_printerr ("Couldn't activate serial service: %s\n", error->message);
    	exit(EXIT_FAILURE);
    }
    
    g_message("Serial Service Activated");
    
    sppManager = dbus_g_proxy_new_for_name(dbusConnection, conn, 
    		"/org/bluez/serial", "org.bluez.serial.Manager");

	if (sppManager == NULL) {
		g_printerr("Couldn't open proxy to serial service\n");
		exit(EXIT_FAILURE);
	}
	
	g_message("Serial Service Proxy initializated");
    
    return;    
}

void openRFCommConnection(DBUS_BTData * data){
	GError *error = NULL;
	
	if(sppManager == NULL) {
		g_printerr("You can't call openRFCommConnection(DBUS_BTData * data) "
				"before calling initSerialService() sorry");
		exit(EXIT_FAILURE);
	}

    if (!dbus_g_proxy_call (sppManager, "ConnectService", &error, 
    		G_TYPE_STRING, data->targetAddr, G_TYPE_STRING, data->service
    				, G_TYPE_INVALID,
    		G_TYPE_STRING, &data->rfcommNode, G_TYPE_INVALID)) {
    	g_printerr ("Couldn't Connect to Device: %s\n", error->message);
    	exit(EXIT_FAILURE);
    }
    
    g_message("Connected to %s", data->rfcommNode);
        
    return;  
}

void closeRFCommConnection(DBUS_BTData * data){
	GError *error = NULL;
	
	if(sppManager == NULL) {
		g_printerr("You can't call closeRFCommConnection(DBUS_BTData * data) "
				"before calling initSerialService() sorry");
		exit(EXIT_FAILURE);
	}

    if (!dbus_g_proxy_call (sppManager, "DisconnectService", &error, 
    		G_TYPE_STRING, data->rfcommNode, G_TYPE_INVALID,
    		G_TYPE_INVALID)) {
    	g_printerr ("Couldn't disconnect to Device: %s\n", error->message);
    	return;
    }
    
    g_message("Disconnected: %s", data->rfcommNode);
        
    return;  
}


void 	closeDBusConnection(){
	dbus_g_connection_unref(dbusConnection);
}

int DBUS_BTConnect(obex_t *handle, void * customdata){
	DBUS_BTData *data;
	
	data = (DBUS_BTData*)OBEX_GetCustomData(handle);
	openRFCommConnection(data);
	
	data->fd = fopen(data->rfcommNode, "ab+"); //+b");
	
	if (data->fd <= 0) {
		g_error("Error opening device: %s\n", data->rfcommNode);
		perror("Desc: ");
		return FALSE;
	} 
	
	g_message("Opened %s", data->rfcommNode);
	
	/*if ( setvbuf (data->fd, NULL, _IONBF, BUFSIZ) != 0) {
		perror("Couldn't set virtual buffer options: ");
	}*/
	
	return TRUE;
}

int DBUS_BTDisconnect(obex_t *handle, void * customdata){
	DBUS_BTData *data;
	
	data = (DBUS_BTData*)OBEX_GetCustomData(handle);
	
	
	fclose(data->fd);
	
	closeRFCommConnection(data);
	
	
	return TRUE;
}

int DBUS_BTListen(obex_t *handle, void * customdata){
	return 0;
}

int DBUS_BTWrite(obex_t *handle, void * customdata, uint8_t *buf, int buflen){
	DBUS_BTData *data;
	int ret, i;
	
	data = (DBUS_BTData*)OBEX_GetCustomData(handle);
	
	/* Return if no fd */
	if(data->fd  == NULL) {
		g_error("No fd!");
		return -1;
	}

	ret =  fwrite (buf, sizeof(uint8_t), buflen, data->fd);
	fflush(data->fd);
	g_message("Wrote %d bytes (expected %d)\n", ret, buflen);
	
	for (i = 0; i <ret ; i++){
		printf("%02X ", buf[i]);
	}
	
	printf("\n");
	
	return ret;
}

int DBUS_BTHandleInput(obex_t *handle, void * customdata, int timeout){
	DBUS_BTData *data;
	int actual, fd;
	struct timeval time;
	fd_set fdset;

	data = (DBUS_BTData*)OBEX_GetCustomData(handle);
	
	/* Return if no fd */
	if(data->fd  == NULL) {
		g_error("No fd!");
		return -1;
	}
	
	fd = fileno (data -> fd);
	
	FD_ZERO(&fdset);
	FD_SET(fd, &fdset);

	time.tv_sec = timeout;
	time.tv_usec = 0;
	
	if (data->buffer == NULL)	
		data->buffer = (char *)calloc(sizeof(char), BUF_SIZE);
	
	//fdatasync(fd);
	
	actual = select(fd, &fdset, NULL, NULL, &time);
	g_message("Select returned %d", actual);
	
	if (actual <= 0)
		return actual;
	
	actual = fread_unlocked (data->buffer, sizeof(char), BUF_SIZE, data->fd);
	
	if(actual <= 0)
		return actual;
	
	g_message("Read %d bytes\n", actual);

	OBEX_CustomDataFeed(handle, (uint8_t *) data->buffer, actual);
	return actual;
}

DBUS_BTData *initDBUS_BT(const char * addr, const char * service, const char *hci){
	DBUS_BTData *out;
	char * temp;
	
	temp = calloc(sizeof(char), strlen(service)+1);
	strcpy(temp, service);
	
	out = (DBUS_BTData *)malloc(sizeof(DBUS_BTData));
	
	out->hciProxy = findAdapter(dbusConnection, hci);	
	out->service = temp;
	out->rfcommNode = NULL;
	out->fd = NULL;
	out->buffer = NULL;
	
	temp = calloc(sizeof(char), strlen(addr)+1);
	strcpy(temp, addr);
	out->targetAddr = temp;
	return out;
}


int main2(int argc, char* argv[]){
	if ( argc < 2) {
		fprintf(stdout, "Usage: %s <address> [service] [command]\n", argv[0]);
		fprintf(stdout, "	<address>: Bluetooth address to use in the XX:XX:XX:XX:XX:XX way\n");
		fprintf(stdout, "	[service]: Bluetooth channel or service to use, default ftp\n");
		
		return 0;
	}
	
	char * serv;
	
	initDBusConnection();
	initSerialService();
	
	if ( argv[2] != NULL )
		serv = argv[2];
	else 
		serv = "ftp";
	
	DBUS_BTData* data = initDBUS_BT( argv[1], serv, NULL );
	
	openRFCommConnection(data);
	/*
	//data->fd = open(data->rfcommNode, O_RDWR);
	int ret;
	//ret = write(data->fd, "AT\n\r", 4);
	
	g_message("Wrote %d bytes (expected %d)\n", ret, 4);
	
	int actual;
	struct timeval time;
	
	fd_set fdset;

	time.tv_sec = 100;
	time.tv_usec = 0;

	FD_ZERO(&fdset);
	FD_SET(data->fd, &fdset);

	ret = select(data->fd +1, &fdset, NULL, NULL, &time);
	
	/* Check if this is a timeout (0) or error (-1) */
	/*if (ret < 1) {
		g_error("Timeout or error (%d)\n", ret);
		return ret;		
	}
	
	if (data->buffer == NULL)	
		data->buffer = (char *)calloc(sizeof(char), BUF_SIZE);
	
	actual = read(data->fd, (data->buffer), BUF_SIZE);
	
	if(actual <= 0)
		return actual;
	
	g_message("Read %d bytes", actual);
	g_message("%s", data->buffer);
	*/
	return 0;
}
