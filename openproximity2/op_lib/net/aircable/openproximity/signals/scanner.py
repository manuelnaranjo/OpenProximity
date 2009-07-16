#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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

BASE_SIGNAL = 100
MAX_SIGNAL = BASE_SIGNAL + 200

DONGLES_ADDED=BASE_SIGNAL 
NO_DONGLES=BASE_SIGNAL+1

CYCLE_COMPLETE=BASE_SIGNAL+20
CYCLE_START=BASE_SIGNAL+21
CYCLE_SCAN_DONGLE=BASE_SIGNAL+22

FOUND_DEVICE=BASE_SIGNAL+30

TEXT = {
	DONGLES_ADDED:		'Dongles added',
	NO_DONGLES: 		'No dongles to add',
	
	CYCLE_COMPLETE: 	'Scan cycle completed',
	CYCLE_START:		'Scan cycle start',
	CYCLE_SCAN_DONGLE:	'Scan cycle on dongle',
	
	FOUND_DEVICE:		'Found device',
}

POST = {
	DONGLES_ADDED:		'scanner_dongle_added',
	NO_DONGLES: 		'scanner_no_dongle',
	
	CYCLE_COMPLETE: 	'scanner_cycle_complete',
	CYCLE_START:		'scanner_cycle_start',
	CYCLE_SCAN_DONGLE:	'scanner_cycle_scan_start',
	
	FOUND_DEVICE:		'scanner_cycle_found_device',
}
