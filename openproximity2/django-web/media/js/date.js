function fix_datetime(original, offset) {
    // convert to msec
    // add local time zone offset
    // get UTC time in msec
    utc = original.getTime() + (original.getTimezoneOffset() * 60000);
   
    // create new Date object for different city
    // using supplied offset
    nd = new Date(utc + (3600000*offset));
   
    // return time as an object
    return nd;

}


function fix_datetime_p(element, time_zone){
    var date_element=getFirstElementByTagAndClassName(null, "vDateField", element);
    var time_element=getFirstElementByTagAndClassName(null, "vTimeField", element);
    var date=date_element.value;
    var time=time_element.value;
    
    var original_date=isoTimestamp(date+"T"+time+"Z");
    var new_date = fix_datetime(original_date, time_zone);
    
    date_element.value=new_date.getISODate();
    time_element.value=new_date.getHourMinuteSecond();
}

function fix_change_form(){
    // if the form has a time_zone field then we have to adjust to the user time zone
    // don't use browser settings! use admin settings. (is this DST safe? :S)
    if ($('time_zone')==null)
      return;

    var time_zone = getNodeAttribute($('time_zone'), "value").replace(/[\(\)]/g, '');
    time_zone=parseFloat(time_zone.replace('GMT', ''))/100;
        
    var i;
    var elements = getElementsByTagAndClassName(null, "datetime");
    
    for (i in elements){
	fix_datetime_p(elements[i], time_zone);
    }
}

function fix_datetime_div(element, time_zone){
    var date=isoTimestamp(element.innerHTML);
    var new_date = fix_datetime(date, time_zone);
    
    element.innerHTML=new_date.toLocaleString();
}

function fix_change_list(){
    // if the form has a time_zone field then we have to adjust to the user time zone
    // don't use browser settings! use admin settings. (is this DST safe? :S)
    if ($('time_zone')==null)
      return;

    var time_zone = getNodeAttribute($('time_zone'), "value").replace(/[\(\)]/g, '');
    time_zone=parseFloat(time_zone.replace('GMT', ''))/100;
        
    var i;
    var elements = getElementsByTagAndClassName(null, "datetimezulu");
    
    for (i in elements){
	fix_datetime_div(elements[i], time_zone);
    }
}


addLoadEvent(fix_change_form);
addLoadEvent(fix_change_list);
