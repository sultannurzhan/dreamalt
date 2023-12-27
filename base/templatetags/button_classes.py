from django import template

register = template.Library()

@register.simple_tag
def button_classes(post, user):
    return 'liked' if post.is_liked(user) else ''