from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dictionary lookup by key in templates. 
       Usage: {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key) 