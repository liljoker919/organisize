from django import template

register = template.Library()

@register.filter
def has_voted(activity, user):
    return activity.voted_users.filter(pk=user.pk).exists()

@register.filter
def dict_lookup(dictionary, key):
    """Lookup a value in a dictionary by key"""
    return dictionary.get(key)