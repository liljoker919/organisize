from django import template

register = template.Library()

@register.filter
def has_voted(activity, user):
    return activity.voted_users.filter(pk=user.pk).exists()