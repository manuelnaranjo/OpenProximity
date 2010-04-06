#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009 Naranjo Manuel Francisco <manuel@aircable.net>
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

from django import template

register = template.Library()

@register.inclusion_tag("MochiKit.js")
def MochiKit():
    return {}

@register.inclusion_tag("log.html")
def Tweet(element, 
        field='pk', 
        url='./', 
        line_format='post.pk + " " + post.fields', 
        interval=5000, 
        amount=100, 
        first_amount=5):

    return {
	    'element': element,
	    'field': field,
	    'url': url,
	    'amount': amount,
	    'interval': interval,
	    'line_format': line_format,
	    'first_amount': first_amount,
	}

