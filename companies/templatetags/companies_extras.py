from django import template

register = template.Library()

@register.filter
def split_comma(value):
    """
    Converts a string like 'A, B' → ['A', 'B'].
    Handles None safely and trims whitespace.
    """
    if not value:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]
