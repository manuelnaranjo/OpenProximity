//
//  OpenProximity javascript library
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

// for IE
if (!window.console) console = {
    log: function() {}
};

// strings that will later be translated
var LOADING="Loading";
var REFRESH="Refresh";
var DELETE="Delete";
var DELETE_MSG="You sure you want to delete?";
var ADMIN_LOG="You need to be loged as admin first";
var CONFIGURE="Configure";
var SERVER_VERSION="server version";
var RUNNING_VERSION="running version";
var NEW_VERSION_AVAILABLE="There's a new version available";
var NEW_VERSION="New Version";
var YOUR_VERSION="Your Version";

// replaced by template
var current_version = "TBD";

// DOM functions
function update_field(el, val){
    getElement(el).innerHTML=val
}
    
function update_field_complex(el, id, val){
    getElement(el+'_'+id).innerHTML=val
}

function create_td(id, content){
    return $("<td />").attr("id", id).text(content);
}

function create_tr_seen(content){
    var tr=TR();
    var td;
    tr.id='seen_' + content.address;
    var fields=['address', 'name', 'last_seen'];//, 'devclass'];
    
    for (i in fields){
        td=TD();
        td.innerHTML=content[fields[i]];
        tr.appendChild(td);
    }
    update_info(content.address);
    return tr;
}

function create_button(id, text, href, bgColor){
    if (bgColor==null)
        bgColor="#e4e4e4";

    var inner;
    var out;
    var a;
    out=DIV({'id': id, 'class':'nav_button'})
    inner=DIV({'class': 'inner', 'style': 'height: 1.5em'})
    out.appendChild(inner)
    a=A({ 'href': href, 'innerHTML': text })
    inner.appendChild(a)
    roundElement(out, {bgColor: bgColor})
    return out
}

function update_known_dongles(dongles){
    var old_body=$('#known tbody');
    var new_body=$("<tbody />");
    var val, tr, td;

    for (var i = 0; i<dongles.length; i++){
        val = dongles[i];
        new_body.append(
                $("<tr />").
                    attr("class", "rpc_dongles").
                    attr("id", "rpc_dongles_"+val.address).
                    append(create_td('dongle_address', val.address)).
                    append(create_td('dongle_scan', val.isScanner)).
                    append(create_td('dongle_scan_enabled', val.scan_enabled)).
                    append(create_td('dongle_scan_priority', val.scan_pri)).
                    append(create_td('dongle_upload', val.isUploader)).
                    append(create_td('dongle_upload_enabled', val.upload_enabled)).
                    append(create_td('dongle_upload_maxconn', val.max_conn)).
                    append(
                        $("<div />").
                            attr("id", 'configure_'+val.address).
                            attr("address", val.address).
                            text(CONFIGURE).
                            attr("onclick", 'do_dongle_configure(this);').
                        addClass("button").addClass("corners").corner()
                    )
        );
    }
    old_body.remove()
    $("#known").append(new_body);
}

function roundedCornersOnLoad() {
    // will round the borders of the needed classes on load
    roundClass(null, "wrapper", null);
    roundClass(null, 'nav_button');
    roundClass(null, 'footer', null);
    roundClass(null, 'btn', {bgColor: "#e4e4e4", color: "#A6D5E9"});
    if (/MSIE/.test(navigator.userAgent))
        return;

    roundClass(null, 'nav_button_grey', {bgColor: '#e4e4e4'});
    roundClass(null, 'userinfo', {corners: 'bl br'});
    roundClass(null, 'content-main', null); 
    roundClass(null, 'plugins', {corners: 'bl br'});
    roundClass(null, 'rounded-white', {bgColor: "#e4e4e4", color: "white"});
}


// AJAX functions
function update_seen_info(address){
    $.ajax('/rpc/device-info?address='+address, {
        'cache': false,
        'success': function(stats){
            var i, td;
            var fields=['valid', 'timeout', 'rejected', 'accepted'];

            t=$('#seen_' + address);

            for ( i in fields){
                td = TD();
                td.innerHTML=stats[fields[i]];
                t.appendChild(td);
            }

        }
    });
}

function update_seen_table(){
    $.ajax('/rpc/last-seen',{
        'cache': false,
        'success': function(stats){
            var i;

            t=$('#last_seen_body');
            replaceChildNodes(t);
            for ( i in stats){
                tr=create_tr_seen(stats[i]);
                t.appendChild(tr);
            }
        }
    });
}

function update_stats(){
    $.ajax('rpc/stats', {
        'cache': false,
        'success': function(stats){
            var td;

            $("#stats_seen").text(stats.seen.total);

            for (var addr in stats.seen.perdongle){
                var val = stats.seen.perdongle[addr]
                $("#stats_count_" + val.address).text(val.count);
            }
            
            $("#stats_valid").text(stats.valid);
            $('#stats_valid').text(stats.valid);
            $('#stats_tries').text(stats.tries);
            $('#stats_timeout').text(stats.timeout);
            $('#stats_rejected').text(stats.rejected);
            $('#stats_accepted').text(stats.accepted);
        }
    });
}



function update_rpc_info(){
    $.ajax('rpc/info', {
        'cache': false,
        'success': function(info){
            $('#rpc_running').text(info.running);
            $('#rpc_uploadres').text(info.uploaders);
            $('#rpc_scanners').text(info.scanners);
            if (info.dongles != undefined)
                update_known_dongles(info.dongles);
        }
    });
}

function check_version(){
    var reply=compare_version(current_version);
    var foot =$('#footer .version');
    if (foot.length==0)
        return;
    foot.text(SERVER_VERSION+": " + reply.latest + "\n"+ RUNNING_VERSION +": " + current_version);

    if ( reply.new_available == true ){
        $("#new_version_top").append(
            $("<h1/>").append(
                $("<a/>").
                    attr("href", 
                        'http://wiki.openproximity.org/userdocumentation').
                    attr("target", "_blank").
                    text(NEW_VERSION_AVAILABLE)
            ).append( $("<p/>").text(NEW_VERSION + ": " + reply.latest) ).
            append( $("<p/>").text(YOUR_VERSION + ": " + current_version) )
        ).css("display", "");
    } else
        $("#new_version_top").parent().remove();
}


function popitup(url, format){
    // pops up a window
    if (format == null)
        format='height=200,width=800';
    newwindow=window.open(url,'_blank', format)
    if (window.focus) 
        newwindow.focus();
}


function create_tree(){
    var t = $('#async_tree');
    
    data = {
        "plugins": [
            "themes", "json_data", "ui", "contextmenu",
        ],

        "json_data": {
            "ajax": {
                "url": "data",
                "data": function(n) {
                    var out = {};
                    out['id'] = n.attr ? n.attr("id") : null;
                    return out;
                },
                "type": "POST",
            },
            "async": true,
            "progressive_render": true,
        },
        
        "themes": {
            "dots": false,
        },
        
        "contextmenu": {
            "items": {
                "create": null,
                "rename": null,
                "ccp": null,
                "remove": null,
                "refresh": {
                    "label": REFRESH,
                    "icon": "refresh",
                    "action": function(node){
                        if ( node.hasClass("leaf") == true )
                            return;
                        var tree = $.jstree._reference(node);
                        tree.refresh(node);
                    }
                },
                "delete": {
                    "label": DELETE,
                    "icon": "remove",
                    "action": function(node){
                        if (node.hasClass("deletable") == false)
                            return;
                        var answer = confirm (DELETE_MSG);
                        if ( ! answer )
                            return
                        var id = node[0].id;
                        $("*").css("cursor", "progress");
                        $.post("delete",
                            { id: id },
                            function(json){
                                $("*").css("cursor", "auto");
                                if (json.need_login){
                                    alert(ADMIN_LOG);
                                    return
                                }
                                if (json.deleted){ 
                                    var tree = $.jstree._reference(node);
                                    tree.remove(node[0]); 
                                }
                            }
                        );
                    },
                }
            }
        }
    };
    t.jstree(data);
}

function initialize_tweets(){
    $("#tweets .aircable_manuel").tweet({
        username: "aircable_manuel",
        count: 5,
        refresh_interval: 600,
        avatar_size: 32,
        template: "{avatar}{text}"
    }).bind("full", function(){
        $(this).find(".tweet_text").each(function(i, line){
            line = $(line)
            if (line.text().match(/\[.*\]\s(\S+)\s([^-]+)\s-\s([0-9]+)\scommits/) == null)
                return;

            var t = line.text();
            t = t.match(/\[.*\]\s(\S+)\s([^-]+)\s-\s([0-9]+)\scommits/);
            var a = $("<a/>");
            a.attr('href', t[1]);
            a.attr("target", "_blank");
            a.text(t[2] + " " + t[3] + " commits");
            line.text("");
            line.append(a);
        })
    })

    $("#tweets .aircable_net").tweet({
        username: "aircable_net",
        count: 5,
        refresh_interval: 600,
        avatar_size: 32,
        template: "{avatar}{text}"
    })
}

function ready($){
    var display = $("body").attr("id")
    console.log("ready for " + display);
    
    check_version();
    
    switch (display){
        case "main-page":
            update_stats();
            update_rpc_info();
            initialize_tweets();
            setInterval("update_stats()", 20000);
            setInterval("update_rpc_info()", 30000);
            break;
        case "last-seen":
            update_seen_table();
            setInterval("update_seen_table()", 10000);
            break;
        case "treeview":
            create_tree();
            break;
    }
    $(".corners").corner();

/*    fix_change_form();
    fix_change_list();*/
}

$(document).ready(ready);

/* button callbacks */
function do_dongle_configure(c){
    window.location="/configure/dongle/"+$(c).attr("address")
}

function generic_restart(caption, url, success){
    if ( confirm (caption) == false )
        return;
    $("#loading").show();
    $.ajax({
        url: url,
        success: function() {
            $("#loading").hide();
            alert(success);
        },
        error: function() {
            $("#loading").hide();
            alert("Something failed, check the logs");
        }
    })

}

function reset_stats(){
    generic_restart(
        "Are you sure you want to drop the statistics? This action can't be recovered",
        '/stats/restart',
        "Successfully Deleted!");
}

function reset_server() {
    generic_restart(
        "Are you sure you want to reset the RPC server? Current connections will be dropped",
        '/rpc/server/restart',
        "Successfully Restarted!");
}

