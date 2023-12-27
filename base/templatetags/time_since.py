# myapp/templatetags/time_since.py
from django import template
from django.utils import timezone
import datetime

register = template.Library()


@register.filter
def time_since(value):
    now = timezone.now()
    elapsed_time = now - value
    if elapsed_time <= datetime.timedelta(seconds=60):
        return 'Just now'
    elif elapsed_time <= datetime.timedelta(minutes=60):
        minutes = int(elapsed_time.total_seconds() // 60)
        return "1 minute ago" if minutes == 1 else f"{minutes} minutes ago"
    elif elapsed_time <= datetime.timedelta(hours=24):
        hours = int(elapsed_time.total_seconds() // 3600)
        return "1 hour ago" if hours == 1 else f"{hours} hours ago"
    elif elapsed_time <= datetime.timedelta(days=30):
        days = int(elapsed_time.total_seconds() // 86400)
        return "1 day ago" if days == 1 else f"{days} days ago"
    elif elapsed_time <= datetime.timedelta(days=365):
        months = int(elapsed_time.total_seconds() // 2592000)
        return "1 month ago" if months == 1 else f"{months} months ago"
    else:
        years = int(elapsed_time.total_seconds() // 31104000)
        return "1 year ago" if years == 1 else f"{years} years ago"


register.filter('time_since', time_since)