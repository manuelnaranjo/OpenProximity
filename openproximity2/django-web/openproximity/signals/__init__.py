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
