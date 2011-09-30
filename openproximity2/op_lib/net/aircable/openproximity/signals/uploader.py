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

'''
Uploaders signals
'''

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

PAIR_IN_PROGRESS=BASE_SIGNAL+50
PAIR_SUCCESS=BASE_SIGNAL+51
PAIR_TIMEOUT=BASE_SIGNAL+52
PAIR_REJECT=BASE_SIGNAL+53

TEXT = {
	DONGLES_ADDED:		'Dongles added',
	NO_DONGLES: 		'No dongles to add',
	
	CYCLE_UPLOAD_DONGLE:	'Upload cycle on dongle',
	
	FILE_UPLOADED:		'File succesfully uploaded',
	FILE_FAILED:		'File failed to upload',
	
	SDP_RESOLVED:		'Service found',
	SDP_NORECORD:		'Service not provided',
	SDP_TIMEOUT:		'Failed to retrieve services',

	PAIR_IN_PROGRESS:   'Tryingto pair',
	PAIR_SUCCESS:       'Paired successfully',
	PAIR_TIMEOUT:       'User did\'t reply to pair request',
	PAIR_REJECT:        'Pairing rejected',
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

	PAIR_IN_PROGRESS:	'uploader_pair_start',
	PAIR_SUCCESS:		'uploader_pair_success',
	PAIR_TIMEOUT:		'uploader_pair_timeout',
	PAIR_REJECT:        'uploader_pair_reject'
}
