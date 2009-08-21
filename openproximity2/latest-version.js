var message_show = True

function compare_version(CURRENT_VERSION) {
    var LATEST_VERSION="05312009";
    var a = new Array();
    a.new_available = CURRENT_VERSION != LATEST_VERSION
    a.latest = LATEST_VERSION
    if (a.new_available){
	if (message_show){
	    alert("There's a new version of OpenProximity2 available, for more information on how to upgrade visit http://code.google.com/p/proximitymarketing/")
	    message_show=False
	}
    }
    return a
}
