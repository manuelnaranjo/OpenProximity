var timerID = 0;
    
function reload()
{
    if (timerID)
    {
	clearTimeout(timerID);
    }
    
    var tmp;
    tmp = findSWF("mychart");
    tmp.reload();

    timerID = setTimeout("reload()", 3000);
}


function findSWF(movieName)
{
    if (navigator.appName.indexOf("Microsoft")!= -1)
    {
	return window[movieName];
    }
    else
    {
	return document[movieName];
    }
}																				    timerID  = setTimeout("reload()", 3000);
																	    