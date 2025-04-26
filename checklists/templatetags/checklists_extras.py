# checklists/templatetags/checklists_extras.py
from django import template

register = template.Library()

@register.simple_tag
def get_item(dictionary, key1, key2):
    """
    Template tag to allow accessing a dictionary item using a tuple key (key1, key2).
    Usage: {% get_item my_dict key_part1 key_part2 as value %}
    Returns None if the key is not found or the input is not a dictionary.
    """
    try:
        # Access the dictionary using the tuple (key1, key2) as the key
        return dictionary.get((key1, key2))
    except AttributeError: # Handle case where dictionary is not a dict-like object
        return None
    # .get() handles KeyError implicitly by returning None by default
