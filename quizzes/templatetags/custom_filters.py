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