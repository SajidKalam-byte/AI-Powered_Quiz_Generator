from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    return value.split(delimiter)
    
@register.filter
def startswith(value, prefix):
    """
    Return True if the string value starts with the given prefix.
    """
    return str(value).startswith(str(prefix))