from django import template

register = template.Library()

@register.filter
def has_voted(activity, user):
    return activity.voted_users.filter(pk=user.pk).exists()


@register.filter
def dict_lookup(dictionary, key):
    """Look up a dictionary value by key"""
    return dictionary.get(key)


@register.simple_tag
def vacation_duration(vacation):
    """Calculate vacation duration in days"""
    if vacation.start_date and vacation.end_date:
        return (vacation.end_date - vacation.start_date).days + 1
    return 0

