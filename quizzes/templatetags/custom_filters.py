from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely get item from dictionary"""
    try:
        return dictionary.get(str(key))
    except:
        return None

@register.filter
def div(value, arg):
    """Divide value by arg, with error handling"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by arg, with error handling"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='sub')
def sub(value, arg):
    return value - arg

@register.filter
def split_tags(value, delimiter=','):
    """Split a string by delimiter and return a list of trimmed tags"""
    if not value:
        return []
    try:
        tags = [tag.strip() for tag in str(value).split(delimiter) if tag.strip()]
        return tags
    except:
        return []

@register.filter
def trim(value):
    """Trim whitespace from string"""
    try:
        return str(value).strip()
    except:
        return value