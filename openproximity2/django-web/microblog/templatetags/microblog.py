from django import template

register = template.Library()

@register.inclusion_tag("MochiKit.js")
def MochiKit():
    return {}

@register.inclusion_tag("log.html")
def Tweet(element, field='pk', url='./', line_format='post.pk + " " + post.fields', interval=5000, amount=100, first_amount=5):
    return {
	    'element': element,
	    'field': field,
	    'url': url,
	    'amount': amount,
	    'interval': interval,
	    'line_format': line_format,
	    'first_amount': first_amount,
	}
