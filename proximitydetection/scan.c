/*
 *
 *  Proximity scanning command line application, this is based on a bluez example [1].
 * 
 *  To build this get into Debug and run make.
 *
 *  If it fails then you need to do:
 *  rm ../marshal.c
 *  rm ../marshal.h (make sure you don't delete marshal.list)
 *  glib-genmarshal --prefix=marshal marshal.list --header > marshal.h
 *  glib-genmarshal --prefix=marshal marshal.list --body > marshal.c
 *  gcc `pkg-config --libs --cflags glib-2.0 dbus-1 dbus-glib-1 gthread-2.0` bluetooth.c marshal.c -o bluetooth
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


#include "scan.h"

//internal members
static DBusGConnection * bus = NULL;
static time_t initTime = 0;
static DBusGProxy * manager = NULL;
static GHashTable * dongles;

//internal functions definitions
static int cleanAdapter(proximityScanner * scanner);
static char * findAdapter(DBusGConnection * bus, const char * hci, 
		proximityScanner *scanner);
static int initAdapter(DBusGProxy* adapter);
static int stopPeriodicDiscovery(DBusGProxy * adapter);
static int isPeriodicDiscovery(DBusGProxy * adapter);
static int isPeriodicDiscovery(DBusGProxy * adapter);
static int startPeriodicDiscovery(DBusGProxy * adapter);
static int stopPeriodicDiscovery(DBusGProxy * adapter);
static int initAdapter(DBusGProxy* adapter);
static int cleanTable (void * key, void * value, void * user_data);

//bluez dbus function callbacks
static void remote_device_found(DBusGProxy *object, const char *address, 
		const unsigned int class, const int rssi, gpointer user_data);
static void discovery_started(DBusGProxy *object, gpointer user_data);
static void remote_name_updated(DBusGProxy *object, const char *address, 
		const char *name, gpointer user_data);
static void discovery_completed(DBusGProxy *object, gpointer user_data);
static void remote_name_failed(DBusGProxy *object, const char *address,
		gpointer user_data);
static void hciAdapterRemoved(DBusGProxy *obj, const char *path, gpointer u);


// ----------------------------------------------------------------------------
// external functions implementation

void startScan(proximityScanner * scanner) {
	int ret = 0;
	
    //add marshallers
    dbus_g_object_register_marshaller(marshal_VOID__STRING_UINT_INT, 
    		G_TYPE_NONE, G_TYPE_STRING, G_TYPE_UINT, G_TYPE_INT, 
    		G_TYPE_INVALID);
    dbus_g_object_register_marshaller(marshal_VOID__STRING_STRING, 
    		G_TYPE_NONE, G_TYPE_STRING, G_TYPE_STRING, G_TYPE_INVALID);
    
    //register signals
    dbus_g_proxy_add_signal(scanner->adapter, "RemoteDeviceFound", 
    		G_TYPE_STRING, G_TYPE_UINT, G_TYPE_INT, G_TYPE_INVALID);
    dbus_g_proxy_connect_signal(scanner->adapter, "RemoteDeviceFound", 
    		G_CALLBACK(remote_device_found), scanner, NULL);

    dbus_g_proxy_add_signal(scanner->adapter, "DiscoveryStarted", 
    		G_TYPE_INVALID);
    dbus_g_proxy_connect_signal(scanner->adapter, "DiscoveryStarted", 
    		G_CALLBACK(discovery_started), scanner, NULL);

    dbus_g_proxy_add_signal(scanner->adapter, "DiscoveryCompleted", 
    		G_TYPE_INVALID);
    dbus_g_proxy_connect_signal(scanner->adapter, "DiscoveryCompleted", 
    		G_CALLBACK(discovery_completed), scanner, NULL);

    dbus_g_proxy_add_signal(scanner->adapter, "RemoteNameUpdated", 
    		G_TYPE_STRING, G_TYPE_STRING, G_TYPE_INVALID);
    dbus_g_proxy_connect_signal(scanner->adapter, "RemoteNameUpdated", 
    		G_CALLBACK(remote_name_updated), scanner, NULL);
    
    dbus_g_proxy_add_signal(scanner->adapter, "RemoteNameFailed",
    		G_TYPE_STRING, G_TYPE_INVALID);
    dbus_g_proxy_connect_signal(scanner->adapter, "RemoteNameFailed",
    		G_CALLBACK(remote_name_failed), scanner, NULL);
    
    dbus_g_proxy_add_signal(manager, "AdapterRemoved", 
    		G_TYPE_STRING, G_TYPE_INVALID);
    dbus_g_proxy_connect_signal(manager, "AdapterRemoved",
        		G_CALLBACK(hciAdapterRemoved), dongles, NULL);
    
    //start inquiring
    ret = initAdapter(scanner->adapter);
    
    if (ret != SCAN_OK)
    	scanner->scanError(ret);
}

void stopScan(proximityScanner * scanner) {
	//unregister signals
	dbus_g_proxy_disconnect_signal(scanner->adapter, "RemoteNameUpdated", 
			G_CALLBACK(remote_name_updated), scanner);
	dbus_g_proxy_disconnect_signal(scanner->adapter, "DiscoveryCompleted", 
			G_CALLBACK(discovery_completed), scanner);
	dbus_g_proxy_disconnect_signal(scanner->adapter, "RemoteDeviceFound", 
			G_CALLBACK(remote_device_found), scanner);
	dbus_g_proxy_disconnect_signal(scanner->adapter, "DiscoveryStarted", 
			G_CALLBACK(discovery_started), scanner);
	
	//stop scanning
	stopPeriodicDiscovery(scanner->adapter);
}

proximityScanner *initScanner(const char * hci){
	proximityScanner * out;
	char * path;
	
	out = (proximityScanner *)malloc(sizeof (proximityScanner));
	
	out->buffer = g_hash_table_new_full ( 
			g_str_hash, g_str_equal, free , free);
	
	//let's alert the programmer he needs to explicity start DBus
	if ( bus == NULL ){
		g_message("initScanner will init DBus connection, but you should call "
				"initDBusConnection first\n");
		initDBusConnection();
	}
	
	out->timeout = SCAN_TIMEOUT;
	path = findAdapter(bus, hci, out);
	
	g_hash_table_insert(dongles, path, out);
	
	return out;
}


void destroyScanner(proximityScanner * scanner){
	g_hash_table_destroy(scanner->buffer);
	
	if (scanner->adapter!=NULL)
		cleanAdapter(scanner);
	
	free(scanner);
}

void run_mainloop (void)
{
        GMainContext *ctx;

        ctx = g_main_loop_get_context (loop);

        while (g_main_context_pending (ctx))
                g_main_context_iteration (ctx, FALSE);
}

void initDBusConnection(){
    GError *error = NULL;
    
    if (bus != NULL)
    	return;

    initTime = time(NULL);
    
    g_type_init();
    g_type_init_with_debug_flags (G_TYPE_DEBUG_OBJECTS);
    g_log_set_always_fatal (G_LOG_LEVEL_WARNING);
    loop = g_main_loop_new (NULL, FALSE);

    bus = dbus_g_bus_get(DBUS_BUS_SYSTEM, &error);
    if (error != NULL)
    {
    	//this is a serious error, we can't do anything if we can't connect to dbus
    	g_printerr("Connecting to system bus failed: %s\n", error->message);
    	g_error_free(error);
    	exit(EXIT_FAILURE);
    }
    
    g_message("Connected to DBUS");
    
	if (manager == NULL)
		manager = dbus_g_proxy_new_for_name(bus, "org.bluez", "/org/bluez", 
				"org.bluez.Manager");
    
	if (manager == NULL) {
    	g_printerr("Couldn't connect to BlueZ manager.");
    	exit(EXIT_FAILURE);
    }
	
	g_message("Connected to BlueZ Manager");
    
	if (dongles == NULL)
		 dongles = g_hash_table_new_full ( g_str_hash, g_str_equal, free , NULL);
	
    return;    
}

void 	closeDBusConnection(){
	dbus_g_connection_unref(bus);
}

// ----------------------------------------------------------------------------

// internal functions implementation

// this function will go over the table and clean it if the device has been in the table
// for over TIMEOUT secs
static int cleanTable (void * key, void * value, void * user_data){
	int ret;
	time_t *lastTime;	
	lastTime = value;
	
	ret = (difftime(time(NULL), *lastTime) > SCAN_TIMEOUT );
	
	if ( ret != 0 )
		g_message("Removing %s from the buffer", (char *)key);
	
	
	return ret;		
}

static void remote_device_found(DBusGProxy *object, const char *address, 
		const unsigned int class, const int rssi, gpointer user_data)
{
		time_t * lastTime;
		proximityScanner * scanner = (proximityScanner *)user_data;
		
		//check if we need to tell the other end or not
		lastTime = g_hash_table_lookup( scanner->buffer , address);
				
		if (! (lastTime == NULL || 
				difftime(time(NULL), *lastTime) > scanner->timeout) )
		return;
		
		//g_message("%d - Signal: RemoteDeviceFound(%s, 0x%d, %d)", 
		//		(int)difftime(time(NULL), initTime), address, class, rssi);
		
		if (scanner->deviceDiscovered == NULL)
			return;
		
		int ret = scanner->deviceDiscovered(address);
			
		if (ret == 0) return;
			
		char * name; 
		GError *error = NULL;
		
		//if name is in cache we will get it from there if not the hcid will do
		//it for us
	    if (!dbus_g_proxy_call (scanner->adapter, "GetRemoteName", 
	    		&error,G_TYPE_STRING, address, G_TYPE_INVALID,
	    		G_TYPE_STRING, &name, G_TYPE_INVALID)) {
	    	
	    	if (!dbus_g_error_has_name (error, 
	    			"org.bluez.Error.RequestDeferred")){
	    		g_printerr ("Couldn't get RemoteName: %s\n", error->message);
	    		
	    		if (scanner->scanError != NULL)
	    			scanner->scanError(SCAN_ERROR_NAME_RESOLVE);
	    	} else
	    		g_message("Name will be resolved by the hcid daemon");
	    		
	    	g_error_free (error);
	    } 
	    else {
	    	//Name was in cache, we tell the server
	    	if (scanner->nameResolved != NULL)
	    		scanner->nameResolved(address, name);
	    	
	    	g_free(name);
	    }
	    
	    time_t *now;
	    now = (time_t *) malloc(sizeof(time_t));
	    time(now);
	    
	    char * t;
	    
	    t = (char *) calloc (sizeof(char), strlen(address)+1);
	    
	    sprintf(t, "%s", address);
	    
	    g_hash_table_insert(scanner->buffer, t, now);
	    
	    //let's check the table size, if we go over BUFFER_SIZE
	    int size = g_hash_table_size ( scanner-> buffer );
	    
	    if (size > BUFFER_SIZE)
	    	g_hash_table_foreach_remove( scanner->buffer, cleanTable, NULL );
}

static void discovery_started(DBusGProxy *object, gpointer user_data)
{
		g_message("%d - Signal: DiscoveryStarted()", 
				(int)difftime(time(NULL), initTime) );
}

static void remote_name_updated(DBusGProxy *object, const char *address, 
		const char *name, gpointer user_data)
{
        //g_message("%d - Signal: RemoteNameUpdated(%s, %s)", 
        //		(int)difftime(time(NULL), initTime), address, name);
    
        if (user_data == NULL)
        	return;
        
        proximityScanner * scanner = (proximityScanner *) user_data;
        
        if (scanner->nameResolved==NULL)
        	return;
        
        scanner->nameResolved(address, name);
}

static void discovery_completed(DBusGProxy *object, gpointer user_data)
{
    g_message("%d - Signal: DiscoveryCompleted()", 
        		(int)difftime(time(NULL), initTime));
    
    if (user_data == NULL)
    	return;
    
    proximityScanner * scanner = (proximityScanner *) user_data;
    
    if (scanner->scanError != NULL)
    	scanner->scanError( SCAN_COMPLETED );
}

static void remote_name_failed(DBusGProxy *object, const char *address,
		gpointer user_data) {
		
    g_message("%d - Signal: RemoteNameFailed(%s)", 
        		(int)difftime(time(NULL), initTime), address);
    
    
    if (user_data == NULL)
        	return;
        
    proximityScanner * scanner = (proximityScanner *) user_data;
        
    if (scanner->scanError != NULL)
    	scanner->scanError( SCAN_ERROR_NAME_RESOLVE );
    
}

static void hciAdapterRemoved(DBusGProxy *obj, const char *path, gpointer u){
	g_message("Signal: hciAdapterRemoved(%s)", path);
	
	proximityScanner * scanner = NULL;
	
	scanner = g_hash_table_lookup((GHashTable *) u , path);
	
	if (scanner) {
		if (scanner->scanError != NULL)
			scanner->scanError(SCAN_ERROR_DONGLE_REMOVED);
		
		stopScan(scanner);
	}
}

static int isPeriodicDiscovery(DBusGProxy * adapter){
	GError *error = NULL;
	gboolean reply;
	int ret;
	
	//check if Periodic Discovery is enabled
    if(!dbus_g_proxy_call(adapter, "IsPeriodicDiscovery", &error, G_TYPE_INVALID,
    		G_TYPE_BOOLEAN, &reply, G_TYPE_INVALID)) {
    	g_printerr("Failed to get periodic discovery state: %s\n", error->message);
    	g_error_free(error);
    	return SCAN_ERROR_PERIODIC_DISCOVERY;
    }
    
    if (reply == 0) {
    	g_message("Periodic Discovery is disabled");    	
    	ret =  SCAN_FALSE;    	
    } else {
    	g_message("Periodic Discovery is all ready enabled");
    	ret = SCAN_TRUE;
    }
    
    return ret;

}

static int startPeriodicDiscovery(DBusGProxy * adapter){
	GError *error = NULL;
    if(!dbus_g_proxy_call(adapter, "StartPeriodicDiscovery", &error,
    		G_TYPE_INVALID, G_TYPE_INVALID)) {
    	g_printerr("Failed to enable Periodic Discovery: %s\n", error->message);
    	g_error_free(error);
    	return SCAN_ERROR_PERIODIC_DISCOVERY;
    }
    
    g_message("PeriodicDiscovery has been enabled");
    
    return SCAN_OK;
}

static int stopPeriodicDiscovery(DBusGProxy * adapter){
	GError *error = NULL;
    if(!dbus_g_proxy_call(adapter, "StopPeriodicDiscovery", &error,
    		G_TYPE_INVALID, G_TYPE_INVALID)) {
    	g_printerr("Failed to enable Periodic Discovery: %s\n", error->message);
    	g_error_free(error);
    	return SCAN_ERROR_NOT_STOPPED;
    }
    
    g_message("PeriodicDiscovery has been disabled");
    
    return SCAN_OK;
}

static int cleanAdapter(proximityScanner * scanner){
	int ret = stopPeriodicDiscovery(scanner->adapter);
	
	if (ret & SCAN_ERROR)
		scanner->scanError(ret);
	
	g_free(scanner->adapter);
	
	return 0;
}

static int setPeriodicDiscoveryNameResolving(DBusGProxy * adapter, int resolve_names){
	GError *error = NULL;
    if(!dbus_g_proxy_call(adapter, "SetPeriodicDiscoveryNameResolving", &error,
    		G_TYPE_BOOLEAN,(gboolean) resolve_names, G_TYPE_INVALID, G_TYPE_INVALID)) {
    	g_printerr("Failed SetPeriodicDiscoveryNameResolving(): %s\n", error->message);
    	g_error_free(error);
    	return SCAN_ERROR_PERIODIC_DISCOVERY;
    }
    
    g_message("DiscoveryNameResolving now is: %i", resolve_names);
    return SCAN_OK;
}

static int initAdapter(DBusGProxy* adapter){
	int ret;
	
	
	ret = isPeriodicDiscovery(adapter);

	if (ret == SCAN_FALSE) {
        ret = startPeriodicDiscovery(adapter);
        if (ret & SCAN_ERROR)
        	return ret;
	}
         
	return setPeriodicDiscoveryNameResolving(adapter, 0);
}

static char * findAdapter(DBusGConnection * bus, const char * hci, proximityScanner *scanner){
	GError *error = NULL;
	DBusGProxy * adapter = NULL;
	char * path;
	
	if (manager == NULL) {
		g_printerr("There's no connection to BlueZ so I can't continue\n");
		exit(EXIT_FAILURE);
	}
	
	if (hci == NULL){
		char * adapterStr;
	    if (!dbus_g_proxy_call (manager, "DefaultAdapter", &error, G_TYPE_INVALID,
	    		G_TYPE_STRING, &adapterStr, G_TYPE_INVALID)) {
	    	g_printerr ("Couldn't get default adapter: %s\n", error->message);
	    	g_error_free (error);
	    	free(manager);
	    	return NULL;
	    }
	    
		adapter = dbus_g_proxy_new_for_name(bus, "org.bluez", adapterStr, "org.bluez.Adapter");
		g_message ("Using: %s", adapterStr);
		
		
		path = calloc (sizeof(char), strlen(adapterStr) + 1 );
		sprintf(path, "%s", adapterStr);
		
		g_free( adapterStr );
	} else {
		adapter = dbus_g_proxy_new_for_name(bus, "org.bluez", hci, "org.bluez.Adapter");
		g_message ("Using: %s", hci);
		
		path = calloc (sizeof(char), strlen(hci) + 1 );
		sprintf(path, "%s", hci);
	}
	
	scanner->adapter = adapter;
    return path;
}

// ---------------------------------
// Testing functions

int testDeviceDiscovered(const char *btAddr){
	int reply = (random() > RAND_MAX / 2 ? 1 : 0);

	g_message("%d - Discovered: %s, resolving name? %d" , 
			(int)difftime(time(NULL), initTime), btAddr, reply);
	return  reply ;
}

void testNameResolved(const char * btAddr, const char * name){
	g_message("%d - Resolved name for: %s, name is: %s",  
			(int)difftime(time(NULL), initTime), btAddr, name);
}

void testScanError(int errNumber){
	g_message("Oops: %i", errNumber);
}

#include <unistd.h>
static void* scanningTest(void * scanner) {
	startScan((proximityScanner *)scanner);
	
	//scan for 120 secs
	sleep(120);
	
	stopScan((proximityScanner *)scanner);
	
	g_message("scanningTest thread ended\n");
	return NULL;
}



int main(int argcstatic, char* argv[])
{
        proximityScanner * scanner;
        GThread * threadScanner;
        GError *error = NULL;

        //you need to init glib
        //initDBusConnection does it automatically
        initDBusConnection();
        
        //now init threads support
        //if (!g_thread_supported ()) 
        //	g_thread_init (NULL);
        
        //then init one scanner, in the future we can use multiple dongles
        scanner = initScanner(NULL);
        
        scanner->deviceDiscovered = testDeviceDiscovered;
        scanner->nameResolved = testNameResolved;
        scanner->scanError = testScanError;

        //if scanner is null, then there isn't much we can do
        if (scanner->adapter == NULL)
        	exit(EXIT_FAILURE);

        //we register a new thread, the thread will do the inquiries
        //threadScanner = g_thread_create (scanningTest, scanner, TRUE, &error);
        
        
        //if (error) {
	//    	g_printerr ("Error: %s\n", error->message);
	//    	g_error_free (error);
	//    	exit(EXIT_FAILURE);
        //}
	
	startScan(scanner);
        
        //and launch the app loop
        loop = g_main_loop_new (NULL, FALSE);
        run_mainloop ();
        dbus_g_connection_flush (bus);
        g_main_loop_run (loop);
            
        //this will be called after the main thread ends
        //clean the adapter
        cleanAdapter(scanner);
        
        //and destroy it
        destroyScanner(scanner);
        
        //finally we clean up the dbus connection
        closeDBusConnection();

        return 0;
}

