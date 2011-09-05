//
//  OpenProximity date time handling library
//
//  OpenProximity2.0 is a proximity marketing OpenSource system.
//  Copyright (C) 2011-2008 Naranjo Manuel Francisco <manuel@aircable.net>
//
//  This program is free software; you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation version 2 of the License.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License along
//  with this program; if not, write to the Free Software Foundation, Inc.,
//  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
//
//

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

function getTimeZone(){
    return parseFloat(
        $("#time_zone").
            attr("value").
            replace(/[\(\)]/g, '').
            replace('GMT', ''))/100;
}


function fix_datetime_p(element, time_zone){
    var date_element=element.find("#vDateField");
    var time_element=element.find("#vTimeField");
    var date=date_element.attr("value");
    var time=time_element.attr("value");
    
    var original_date=isoTimestamp(date+"T"+time+"Z");
    var new_date = fix_datetime(original_date, time_zone);
    
    date_element.attr("value", new_date.getISODate());
    time_element.attr("value", new_date.getHourMinuteSecond());
}

function fix_change_form(){
    // if the form has a time_zone field then we have to adjust to the user time zone
    // don't use browser settings! use admin settings. (is this DST safe? :S)
    if ($('#time_zone').length==0)
        return;

    var time_zone = getTimeZone();

    $(".datetime").each(function(i, element){
        fix_datetime_p(element, time_zone);
    })
}

function fix_datetime_div(element, time_zone){
    var date=isoTimestamp(element.text());
    var new_date = fix_datetime(date, time_zone);

    element.text(new_date.toLocaleString());
}

function fix_change_list(){
    // if the form has a time_zone field then we have to adjust to the user time zone
    // don't use browser settings! use admin settings. (is this DST safe? :S)
    if ($('#time_zone').length==0)
        return;

    var time_zone = getTimeZone();

    $(".datetimezulu").each(function(i, element){
        fix_datetime_div(element, time_zone);
    });
}
