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
