from django import template
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.template.context import Context

register = template.Library()

class BoxNode(template.Node):
    def __init__(self, nodelist, table_id):
	self.nodelist = nodelist
	self.table_id = table_id
	
    def render(self, context):
	temp = get_template('bluez/box.html')
	output=self.nodelist.render(context)
	#print self.table_id
	return temp.render(Context(
	    {'content':output,
	    'table_id': str(self.table_id),
	    }))
	

	#return render_to_response('bluez/box.html', { 'content': output })

@register.tag
def box(parser, token):
    try:
	tag_name, table_id = token.split_contents()
    except Exception, err:
	raise template.TemplateSyntaxError("box needs one argument and a block")

    nodelist = parser.parse(('endbox',))
    parser.delete_first_token()
    return BoxNode(nodelist, table_id[1:-1])
