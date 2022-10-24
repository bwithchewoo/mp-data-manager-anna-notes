from django.template.defaulttags import register

# Borrowed directly from culebrón: 
# https://stackoverflow.com/a/8000091/706797

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)