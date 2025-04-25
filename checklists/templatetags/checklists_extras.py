from django import template

register = template.Library()

@register.simple_tag
def get_item(dictionary, key1, key2):
    """Permite aceder a dictionary[(key1, key2)] em templates."""
    try:
        return dictionary[(key1, key2)]
    except (KeyError, TypeError):
        return None 