# checklists/templatetags/checklists_extras.py
from django import template

register = template.Library()

@register.simple_tag
def get_item(dictionary, key1, key2=None):
    """
    Template tag to allow accessing a dictionary item using either a single key (key1)
    or a tuple key (key1, key2).
    
    Usage:
    {% get_item my_dict key_part1 as value %}
    {% get_item my_dict key_part1 key_part2 as value %}
    
    Returns None if the key is not found or the input is not dictionary-like.
    """
    try:
        if key2 is not None:
            # Access using the tuple key if key2 is provided
            key = (key1, key2)
        else:
            # Access using the single key if key2 is not provided
            key = key1
            
        # Use .get() for safe access
        return dictionary.get(key)
        
    except AttributeError:
        # Handle case where dictionary is not a dict-like object
        return None
    except TypeError:
        # Handle case where key is not hashable (less likely here)
        return None
