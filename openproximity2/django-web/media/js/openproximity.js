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

// DOM functions
function update_field(el, val){
    getElement(el).innerHTML=val
}
    
function update_field_complex(el, id, val){
    getElement(el+'_'+id).innerHTML=val
}
	
function create_td(id, content){
    var td = TD({ 'id': id, 'innerHTML': content })
    return td
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

function update_seen_info(address){
    var defer=loadJSONDoc('/rpc/device-info?address='+address);

    var gotDeviceInfo = function(stats){
        var i, td;
        var fields=['valid', 'timeout', 'rejected', 'accepted'];
        //'tries', 
	
        t=getElement('seen_' + address);
	
        for ( i in fields){
            td = TD();
            td.innerHTML=stats[fields[i]];
            t.appendChild(td);
        }
    }
    
    var deviceInfoFailed = function(err){
    }

    defer.addCallbacks(gotDeviceInfo, deviceInfoFailed);
}

function update_seen_table(){
    var defer=loadJSONDoc('/rpc/last-seen');

    var gotLastSeen = function(stats){
        var i;
	
        t=getElement('last_seen_body');
        replaceChildNodes(t);
        for ( i in stats){
            tr=create_tr_seen(stats[i]);
            t.appendChild(tr);
        }
    }
    
    var lastSeenFailed = function(err){
    }

    defer.addCallbacks(gotLastSeen, lastSeenFailed);
}

function update_stats(){
    var defer = loadJSONDoc('rpc/stats');

    var gotStats=function(stats){
        var td;
        
        update_field('stats_seen', stats.seen.total);
        
        for (var addr in stats.seen.perdongle){
            var val = stats.seen.perdongle[addr]
            update_field_complex('stats_count', val.address, val.count);
        }
        
        update_field('stats_valid', stats.valid);
        update_field('stats_tries', stats.tries);
        update_field('stats_timeout', stats.timeout);
        update_field('stats_rejected', stats.rejected);
        update_field('stats_accepted', stats.accepted);
    };

    var statsFetchFailed = function(err){
        /*alert(err)*/
    };
    
    defer.addCallbacks(gotStats, statsFetchFailed);
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
    var old_body=$('known').getElementsByTagName('tbody')[0];
    var new_body=TBODY();
    var val, tr, td;

    for (var i = 0; i<dongles.length; i++){
		val = dongles[i];
		tr = TR({ 
		    'class': 'rpc_dongles', 
		    'id': "rpc_dongles_"+val.address
		});
		tr.appendChild(create_td('dongle_address', val.address));
		tr.appendChild(create_td('dongle_scan', val.isScanner));
		tr.appendChild(create_td('dongle_scan_enabled', val.scan_enabled));
		tr.appendChild(create_td('dongle_scan_priority', val.scan_pri));
		tr.appendChild(create_td('dongle_upload', val.isUploader));
		tr.appendChild(create_td('dongle_upload_enabled', val.upload_enabled));
		tr.appendChild(create_td('dongle_upload_maxconn', val.max_conn));
		td=TD({
		    'style': 'width: 10em;',
		    'id': 'dongle_setup'
		});
		td.appendChild(
		    create_button(
			'configure_'+val.address, 
			"{% trans "Configure" %}",
			'configure/dongle/' + val.address,
			'white'
		    )
		);
		tr.appendChild(td);
		new_body.appendChild(tr);
	}
    swapDOM(old_body, new_body);
}

function update_rpc_info(){
    var defer = loadJSONDoc('rpc/info');

    var gotInfo=function(info){
        update_field('rpc_running', info.running);
        update_field('rpc_uploadres', info.uploaders);
        update_field('rpc_scanners', info.scanners);
        update_known_dongles(info.dongles);
    };

    var infoFetchFailed = function(err){
        /*alert(err)*/
    }
    defer.addCallbacks(gotInfo, infoFetchFailed);
}

function check_version(){
    var reply=compare_version("{{version.current}}");
    var foot =$('version_foot');
    var p=P("{% trans "server version" %}: " + reply.latest + " {% trans "running version" %}: {{ version.current }}");
    foot.appendChild(p)

    if ( reply.new_available == true ){
        var top = $('new_version_top');
        var h1=H1()
        var a = A({ 
                'href': 'http://code.google.com/p/proximitymarketing/',
                'innerHTML': "{% trans "There's a new version available" %}"
        });
        h1.appendChild(a);
        top.appendChild(h1)
        top.appendChild(P("{% trans "New Version" %}: " + reply.latest));
        top.appendChild(P("{% trans "Your Version" %}: {{ version.current }}"));
        top.style.display="";
    }
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

function popitup(url, format){
    // pops up a window
    if (format == null)
        format='height=200,width=800';
	newwindow=window.open(url,'name', format)
	if (window.focus) 
	    newwindow.focus();
}

// strings that will later be translated
var LOADING="Loading";
var REFRESH="Refresh";
var DELETE="Delete";
var DELETE_MSG="You sure you want to delete?";
var ADMIN_LOG="You need to be loged as admin first";

function create_tree(){
    var t = $('#async_tree');
    
    data = {
        data: {
            type: 'json',
            async: true,
            opts: {
                method: "POST",
                url: "data",
            }
        },
        
        ui: {
            dots: false,
            animation: 100,
        },
        
        lang: {
            loading: LOADING + "...";          
        },
        
        plugins: {
            contextmenu: {
                items: {
                    remove: false,
                    rename: false,
                    create: false,
                    refresh: {
                        label: REFRESH,
                        icon: "refresh",
                        visible: function(node, tree){
                            return node.hasClass('leaf') != true;
                        },
                        action: function(node, tree){
                            tree.refresh(node);
                        }
                    },
                    delete: {
                        label: DELETE;
                        icon: "remove",
                        visible: function(node, tree){
                            return node.hasClass('deletable')
                        },
                        action: function(node, tree){
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
                                    if (json.deleted){ tree.remove(node[0]); }
                                }
                            );
                        },
                    }
                }
            }
        }
    };
    t.tree(data);
}




addLoadEvent(update_stats);
addLoadEvent(update_rpc_info);
addLoadEvent(check_version);
addLoadEvent(roundedCornersOnLoad);
addLoadEvent(create_tree);

setInterval("update_stats()", 20000) <!-- update each 20 seconds -->
setInterval("update_rpc_info()", 30000) <!-- update each 30 seconds -->

