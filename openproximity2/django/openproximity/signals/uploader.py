BASE_SIGNAL = 500
MAX_SIGNAL = BASE_SIGNAL + 200

DONGLES_ADDED=BASE_SIGNAL 
NO_DONGLES=BASE_SIGNAL+1

CYCLE_UPLOAD_DONGLE=BASE_SIGNAL+20

FILE_UPLOADED=BASE_SIGNAL+30
FILE_FAILED=BASE_SIGNAL+31

SDP_RESOLVED=BASE_SIGNAL+40
SDP_NORECORD=BASE_SIGNAL+41
SDP_TIMEOUT=BASE_SIGNAL+42

TEXT = {
	DONGLES_ADDED:		'Dongles added',
	NO_DONGLES: 		'No dongles to add',
	
	CYCLE_UPLOAD_DONGLE:	'Upload cycle on dongle',
	
	FILE_UPLOADED:		'File succesfully uploaded',
	FILE_FAILED:		'File failed to upload',
	
	SDP_RESOLVED:		'Service found',
	SDP_NORECORD:		'Service not provided',
	SDP_TIMEOUT:		'Failed to retrieve services'
}

POST = {
	DONGLES_ADDED:		'uploader_dongle_added',
	NO_DONGLES: 		'uploader_no_dongle',
	
	CYCLE_UPLOAD_DONGLE:	'uploader_cycle',
	
	FILE_UPLOADED:		'uploader_success',
	FILE_FAILED:		'uploader_failed',
	
	SDP_RESOLVED:		'uploader_sdp_ok',
	SDP_NORECORD:		'uploader_sdp_no',
	SDP_TIMEOUT:		'uploader_sdp_timeout',
}
