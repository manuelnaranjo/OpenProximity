#	OpenProximity2.0 is a proximity marketing OpenSource system.
#	Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation version 2 of the License.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License along
#	with this program; if not, write to the Free Software Foundation, Inc.,
#	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Agent that pushes data to a central server
def reset_stats(connection):
	from django.db import models
	from django.core.management.color import no_style
	from django.core.management import sql
	tables = [ 
			'agent_agentdevicerecord',
			'agent_agentrecord'
	]
	
	for table in tables:
		connection.cursor().execute("drop table %s" % table)
