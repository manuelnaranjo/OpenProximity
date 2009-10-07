var message_show = 0

function compare_version(CURRENT_VERSION) {
    var LATEST_VERSION="beta-10062009";
    var a = new Array();
    a.new_available = CURRENT_VERSION != LATEST_VERSION
    a.latest = LATEST_VERSION
    if (a.new_available){
        if (message_show==0){
           alert("There's a new version of OpenProximity2 available, for more information on how to upgrade visit http://code.google.com/p/proximitymarketing/wiki/Updates")
           message_show=1
        }
    }
    return a
}
