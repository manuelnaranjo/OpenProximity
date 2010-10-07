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

import scanner
import uploader

TEXT={
	scanner.BASE_SIGNAL: 'Scanner signals',
	uploader.BASE_SIGNAL: 'Uploader signals',
}

def __isSignal(kind, signal):
	return signal>=kind.BASE_SIGNAL and signal <= kind.MAX_SIGNAL
	
def isScannerSignal(signal):
	return __isSignal(scanner, signal)

def isUploaderSignal(signal):
	return __isSignal(uploader,signal)
