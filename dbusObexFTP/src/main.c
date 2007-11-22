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

#include <getopt.h>
#include <openobex/obex.h>
#include "dbus-binding.h"

#define VERSION "0.1"

/* create global uuid buffers */
static const uint8_t *fbs_uuid = (const uint8_t *)UUID_FBS;
static const uint8_t *irmc_uuid = (const uint8_t *)UUID_IRMC;
static const uint8_t *s45_uuid = (const uint8_t *)UUID_S45;
static const uint8_t *pcsoftware_uuid = (const uint8_t *)UUID_PCSOFTWARE;


static int c;
static obexftp_client_t *cli = NULL;
static const char *hci = NULL;
static char *addr = NULL;
static char *service = NULL;
static const uint8_t *use_uuid = (const uint8_t *)UUID_FBS;
static int use_uuid_len = sizeof(UUID_FBS);
static int use_conn=1;
static int use_path=1;




/* connect with given uuid. re-connect every time */
static int cli_connect_uuid(const uint8_t *uuid, int uuid_len)
{
	if (cli == NULL) {
		obex_ctrans_t ctrans;
		
		initDBusConnection();
		initSerialService();
			
		if ( service == NULL )		
			service = "ftp";
		
		DBUS_BTData* data = initDBUS_BT( addr, service, hci );
			
		//data->targetAddr = addr;

		ctrans.connect = DBUS_BTConnect;
		ctrans.disconnect = DBUS_BTDisconnect;
		ctrans.listen = NULL;
		ctrans.write = DBUS_BTWrite;
		ctrans.handleinput = DBUS_BTHandleInput;
		ctrans.customdata = data;
		
		/* Open */
		cli = obexftp_open (OBEX_TRANS_DBUS_BLUETOOTH, &ctrans, NULL, NULL);
		
		if(cli == NULL) {
			fprintf(stderr, "Error opening obexftp-client\n");
			exit(1);
			//return FALSE;
		}
		if (!use_conn) {
			cli->quirks &= ~OBEXFTP_CONN_HEADER;
		}
		if (!use_path) {
			cli->quirks &= ~OBEXFTP_SPLIT_SETPATH;
		}
	}	
	
	DBUS_BTData* data;
	
	data = (DBUS_BTData*)cli->ctrans->customdata;
	/* Connect */
	OBEX_SetCustomData(cli->obexhandle, data);
	
	if (obexftp_connect_uuid(cli, NULL, 0, uuid, uuid_len) >= 0)
    		return TRUE;
	fprintf(stderr, "Still trying to connect\n");
	

	obexftp_close(cli);
	cli = NULL;
	return FALSE;
}

static int cli_connect () {
	
	if (cli != NULL) {
		return TRUE;
	}

	if (!cli_connect_uuid(use_uuid, use_uuid_len))
		exit(1);

	return TRUE;
}

static void cli_disconnect()
{
	if (cli != NULL) {
		/* Disconnect */
		(void) obexftp_disconnect (cli);
		/* Close */
		obexftp_close (cli);
		cli = NULL;
	}
}

static int parse_uuid(char *name, const uint8_t **uuid, int *uuid_len)
{
	if (name == NULL || *name == '\0' ||
			!strncasecmp(name, "none", 4) ||
			!strncasecmp(name, "null", 4) ||
			!strncasecmp(name, "push", 4) ||
			!strncasecmp(name, "goep", 4)) {
		fprintf(stderr, "Suppressing FBS.\n");
		if (uuid) *uuid = NULL;
		if (uuid_len) *uuid_len = 0;
		return 0;
	}

        if (!strncasecmp(name, "fbs", 3) || !strncasecmp(name, "ftp", 3)) {
		fprintf(stderr, "Using FBS uuid.\n");
		if (uuid) *uuid = fbs_uuid;
		if (uuid_len) *uuid_len = sizeof(UUID_FBS);
		return sizeof(UUID_FBS);
	}

        if (!strncasecmp(name, "sync", 4) || !strncasecmp(name, "irmc", 4)) {
		fprintf(stderr, "Using SYNCH uuid.\n");
		if (uuid) *uuid = irmc_uuid;
		if (uuid_len) *uuid_len = sizeof(UUID_IRMC);
		return sizeof(UUID_IRMC);
	}

        if (!strncasecmp(name, "s45", 3) || !strncasecmp(name, "sie", 3)) {
		fprintf(stderr, "Using S45 uuid.\n");
		if (uuid) *uuid = s45_uuid;
		if (uuid_len) *uuid_len = sizeof(UUID_S45);
		return sizeof(UUID_S45);
	}
	
        if (!strncasecmp(name, "pcsoftware", 10) || !strncasecmp(name, "sharp", 5)) {
		fprintf(stderr, "Using PCSOFTWARE uuid.\n");
		if (uuid) *uuid = pcsoftware_uuid;
		if (uuid_len) *uuid_len = sizeof(UUID_PCSOFTWARE);
		return sizeof(UUID_PCSOFTWARE);
	}

	return -1;
}


int main(int argc, char *argv[])
{
	int verbose=0;
	int most_recent_cmd = 0;
	char *output_file = NULL;
	char *move_src = NULL;

	/* preset mode of operation depending on our name */
	if (strstr(argv[0], "ls") != NULL)	most_recent_cmd = 'l';
	if (strstr(argv[0], "get") != NULL)	most_recent_cmd = 'g';
	if (strstr(argv[0], "put") != NULL)	most_recent_cmd = 'p';
	if (strstr(argv[0], "rm") != NULL)	most_recent_cmd = 'k';       

	while (1) {
		int option_index = 0;
		static struct option long_options[] = {
			{"bluetooth",		required_argument, NULL, 'b'},
			{"service",	required_argument, NULL, 'B'},
			{"hci",				required_argument, NULL, 'd'},
			{"uuid",	optional_argument, NULL, 'U'},
			{"noconn",	no_argument, NULL, 'H'},
			{"nopath",	no_argument, NULL, 'S'},
			{"list",	optional_argument, NULL, 'l'},
			{"chdir",	required_argument, NULL, 'c'},
			{"mkdir",	required_argument, NULL, 'C'},
			{"output",	required_argument, NULL, 'o'},
			{"get",		required_argument, NULL, 'g'},
			{"getdelete",	required_argument, NULL, 'G'},
			{"put",		required_argument, NULL, 'p'},
			{"delete",	required_argument, NULL, 'k'},
			{"capability",	no_argument, NULL, 'X'},
			{"probe",	no_argument, NULL, 'Y'},
			{"info",	no_argument, NULL, 'x'},
			{"move",	required_argument, NULL, 'm'},
			{"verbose",	no_argument, NULL, 'v'},
			{"version",	no_argument, NULL, 'V'},
			{"help",	no_argument, NULL, 'h'},
			{"usage",	no_argument, NULL, 'h'},
			{0, 0, 0, 0}
		};
		
		c = getopt_long (argc, argv, "-ib::B:d:u::t:n:U::HSL::l::c:C:f:o:g:G:p:k:XYxm:VvhN:FP",
				 long_options, &option_index);
		if (c == -1)
			break;
	
		if (c == 1)
			c = most_recent_cmd;
	
		switch (c) {
		
		case 'b':
			/* handle severed optional option argument */
			if (!optarg && argc > optind && argv[optind][0] != '-') {
				optarg = argv[optind];
				optind++;
			}
       		addr = optarg;
			break;
			
		case 'B':
			service = optarg;
			break;
			
		case 'd':
			hci = optarg;
			break;
			
		case 'F':
			fprintf(stderr,"Option -%c is deprecated, use -%c instead\n",'F','U');
			optarg = "none";
		case 'U':
			/* handle severed optional option argument */
			if (!optarg && argc > optind && argv[optind][0] != '-') {
				optarg = argv[optind];
				optind++;
			}
			if (parse_uuid(optarg, &use_uuid, &use_uuid_len) < 0)
				fprintf(stderr, "Unknown UUID %s\n", optarg);
			break;

		case 'H':
			use_conn=0;
			break;

		case 'S':
			use_path=0;
			break;

		case 'L':
			/* handle severed optional option argument */
			if (!optarg && argc > optind && argv[optind][0] != '-') {
				optarg = argv[optind];
				optind++;
			}
			if(cli_connect ()) {
				/* List folder */
				stat_entry_t *ent;
				void *dir = obexftp_opendir(cli, optarg);
				while ((ent = obexftp_readdir(dir)) != NULL) {
					stat_entry_t *st;
					st = obexftp_stat(cli, ent->name);
					if (!st) continue;
					printf("%d %s%s\n", st->size, ent->name,
						ent->mode&S_IFDIR?"/":"");
				}
				obexftp_closedir(dir);
			}
			most_recent_cmd = c;
			break;

		case 'l':
			/* handle severed optional option argument */
			if (!optarg && argc > optind && argv[optind][0] != '-') {
				optarg = argv[optind];
				optind++;
			}
			if(cli_connect ()) {
				/* List folder */
				(void) obexftp_list(cli, NULL, optarg);
			}
			most_recent_cmd = c;
			break;

		case 'c':
			if(cli_connect ()) {
				/* Change dir */
				(void) obexftp_setpath(cli, optarg, 0);
			}
			most_recent_cmd = c;
			break;

		case 'C':
			if(cli_connect ()) {
				/* Change or Make dir */
				(void) obexftp_setpath(cli, optarg, 1);
			}
			most_recent_cmd = c;
			break;

		case 'o':
			output_file = optarg;
			break;

		case 'g':
		case 'G':
			if(cli_connect ()) {
				char *p; /* basename or output_file */
				if ((p = strrchr(optarg, '/')) != NULL) p++;
				else p = optarg;
				if (output_file) p = output_file;
				/* Get file */
				if (obexftp_get(cli, p, optarg) && c == 'G')
					(void) obexftp_del(cli, optarg);
				output_file = NULL;
			}
			most_recent_cmd = c;
			break;

		case 'p':
			if(cli_connect ()) {
				char *p; /* basename or output_file */
				if ((p = strrchr(optarg, '/')) != NULL) p++;
				else p = optarg;
				if (output_file) p = output_file;
				/* Send file */
				(void) obexftp_put_file(cli, optarg, p);
				output_file = NULL;
			}
			most_recent_cmd = c;
			break;

		case 'k':
			if(cli_connect ()) {
				/* Delete file */
				(void) obexftp_del(cli, optarg);
			}
			most_recent_cmd = c;
			break;
			
		case 'm':
			most_recent_cmd = c;

			if (move_src == NULL) {
				move_src = optarg;
				break;
			}
			if(cli_connect ()) {
				/* Rename a file */
				(void) obexftp_rename(cli, move_src, optarg);
			}
			move_src = NULL;
			break;

		case 'v':
			verbose++;
			break;
			
		case 'V':
			printf("DBUSObexFTP %s\n", VERSION);
			most_recent_cmd = 'h'; // not really
			break;

		case 'h':
			printf("dbusObexFTP %s\n", VERSION);
			printf("Usage: %s [ -b <dev> [-B <chan>] [-d <hci>]| -U <intf> ]\n"
				"[-c <dir> ...] [-C <dir> ] [-l [<dir>]]\n"
				"[-g <file> ...] [-p <files> ...] [-k <files> ...] [-x] [-m <src> <dest> ...]\n"
				"Transfer files from/to Mobile Equipment.\n"
				"Copyright (c) 2007 Naranjo Manuel Francisco <manuel@aircable.net>\n"
				"Copyright (c) 2002-2004 Christian W. Zuckschwerdt\n"
				"\n"
				" -b, --bluetooth [<device>]  use or search a bluetooth device\n"
				" [ -B, --service <service/number> ]  use this bluetooth service/channel \n"
				"\t\t\twhen connecting\n"
				" [ -d, --hci <string> ]  	  give this as: /org/bluez/hci# \n"
				" -U, --uuid                  use given uuid (none, FBS, IRMC, S45, SHARP)\n"
				" -H, --noconn                suppress connection ids (no conn header)\n"
				" -S, --nopath                dont use setpaths (use path as filename)\n\n"
				" -c, --chdir <DIR>           chdir\n"
				" -C, --mkdir <DIR>           mkdir and chdir\n"
				" -l, --list [<FOLDER>]       list current/given folder\n"
				" -o, --output <PATH>         specify the target file name\n"
				"                             get and put always specify the remote name.\n"
				" -g, --get <SOURCE>          fetch files\n"
				" -G, --getdelete <SOURCE>    fetch and delete (move) files \n"
				" -p, --put <SOURCE>          send files\n"
				" -k, --delete <SOURCE>       delete files\n\n"
				" -m, --move <SRC> <DEST>     move files (Siemens)\n\n"
				" -v, --verbose               verbose messages\n"
				" -V, --version               print version info\n"
				" -h, --help, --usage         this help text\n"
				"\n",
				argv[0]);
			most_recent_cmd = 'h'; // not really
			break;

		default:
			printf("Try `%s --help' for more information.\n",
				 argv[0]);
		}
	}

	if (most_recent_cmd == 0)
	       	fprintf(stderr, "Nothing to do. Use --help for help.\n");

	if (optind < argc) {
		fprintf(stderr, "non-option ARGV-elements: ");
		while (optind < argc)
			fprintf(stderr, "%s ", argv[optind++]);
		fprintf(stderr, "\n");
	}

	cli_disconnect ();

	exit (0);

}
