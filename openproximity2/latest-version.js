function compare_version(CURRENT_VERSION) {
    var LATEST_VERSION="05312009";
    var a = new Array();
    a.new_available = CURRENT_VERSION != LATEST_VERSION
    a.latest = LATEST_VERSION
    return a
}
